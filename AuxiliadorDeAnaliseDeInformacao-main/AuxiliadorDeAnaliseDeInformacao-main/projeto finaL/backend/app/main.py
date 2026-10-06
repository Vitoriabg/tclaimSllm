from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from ddgs import DDGS
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .criticidade import montar
from .instagram import obter_legenda_instagram
from .nlp_pipeline import analisar_texto


class VerificacaoEntrada(BaseModel):
    sentenca: str


MODEL_PATH = Path(__file__).resolve().parent.parent / "modelo_pipeline_completo.pkl"
modelo = joblib.load(MODEL_PATH)
COLUNAS = list(modelo.feature_names_in_)  # ordem exata usada no treino

MAX_CHARS = 6000
MAX_SENTENCAS = 80

app = FastAPI(title="API de análise de sentenças")

# Depois do deploy, troque "*" pelo domínio da Vercel, ex.: ["https://meu-site.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Entrada(BaseModel):
    url: Optional[str] = None    # link de post/reel do Instagram
    texto: Optional[str] = None  # ou o texto direto


@app.get("/")
@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/analisar")
def analisar(e: Entrada):
    texto = (e.texto or "").strip()
    origem = "texto"

    if not texto and e.url:
        texto, status = obter_legenda_instagram(e.url)
        origem = "instagram"
        if texto is None:
            raise HTTPException(422, f"{status}. Cole o texto da legenda no campo de texto.")

    if not texto:
        raise HTTPException(400, "Envie 'url' ou 'texto'.")

    texto = texto[:MAX_CHARS]
    linhas = analisar_texto(texto)[:MAX_SENTENCAS]
    if not linhas:
        raise HTTPException(422, "Nenhuma sentença encontrada.")

    df = pd.DataFrame(linhas)[COLUNAS]
    probas = modelo.predict_proba(df)
    classes = [c.item() if hasattr(c, "item") else c for c in modelo.classes_]

    resultado = []
    for l, p in zip(linhas, probas):
        i = int(p.argmax())
        resultado.append({
            "sentenca_original": l["sentenca_original"],
            "sentenca_corrigida": l["sentenca"],
            "classe": classes[i],
            "confianca": float(p[i]),
            "probabilidades": {str(c): float(x) for c, x in zip(classes, p)},
        })

    return {"origem": origem, "classes": classes, "total": len(resultado), "sentencas": resultado}


@app.post("/api/verificar")
def verificar_claim(entrada: VerificacaoEntrada):
    claim = entrada.sentenca.strip()[:1000]
    if not claim:
        raise HTTPException(400, "Sentença vazia.")

    # 1. Pesquisa na internet (retrieval)
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(claim, region="br-pt", max_results=8))
    except Exception as e:
        print("ERRO NA BUSCA:", e)
        raise HTTPException(502, "Falha ao pesquisar na internet. Tente novamente.")

    fontes = [r for r in resultados if r.get("href")]
    if not fontes:
        return {"sem_fontes": True}

    # 2. Apoio ao pensamento crítico por regras e templates (sem LLM)
    return montar(claim, fontes)
