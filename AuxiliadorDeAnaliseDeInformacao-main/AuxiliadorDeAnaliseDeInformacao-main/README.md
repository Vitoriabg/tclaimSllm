# Detector de Claim
# Equipe: 
Octopus
# Membros: 
Jhenyfer da Silva Souza, 
Lucas Anand Mazotti Ferretti, 
Tárcio A. C. Quissanga,
Gabriel Passarela Silva,
Matheus Vasconcellos da Silva,
Vitória Pereira Bagatin;

# Detector de Claims

Aplicação web que identifica, em um texto, as frases que afirmam algo verificável (claims). Ao clicar em uma claim, o usuário recebe um cartão de apoio ao pensamento crítico: tipo da afirmação, o que precisaria ser verdade, perguntas para investigar, alertas sobre as fontes e como checar por conta própria. O sistema **não** diz se a afirmação é verdadeira ou falsa, e a verificação **não usa LLM**.

Equipe Octopus.

## Como funciona

1. **`/api/analisar`**: divide o texto em sentenças (spaCy) e um modelo de aprendizado de máquina (`modelo_pipeline_completo.pkl`) classifica cada uma como Claim ou Não-Claim.
2. **`/api/verificar`**: pesquisa a frase no DuckDuckGo e monta o cartão com regras e templates (`criticidade.py`).

O front-end (HTML/CSS/JS puros) conversa com a API em `http://localhost:7860`.

## Estrutura de pastas

O `main.py` usa imports relativos e procura o modelo **uma pasta acima** dele. Organize assim:

```
projeto/
├── modelo_pipeline_completo.pkl
├── requirements.txt
├── app/                      # pacote da API (o nome pode ser outro)
│   ├── __init__.py
│   ├── main.py
│   ├── criticidade.py
│   ├── nlp_pipeline.py
│   └── instagram.py
└── frontend/
    ├── index.html
    ├── style.css
    ├── script.js
    ├── polvo.css
    ├── polvo.js
    ├── polvo-branco.png
    └── logo.png
```

Se você usar outro nome no lugar de `app`, troque também no comando de execução abaixo.

## Requisitos

- Python 3.10 ou superior
- A mesma versão do `scikit-learn` usada para treinar o `.pkl` (versões diferentes podem dar erro ou avisos ao carregar o modelo)
- Acesso à internet (busca no DuckDuckGo e download do modelo do spaCy)

## Instalação

Na pasta `projeto/`:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
```

O modelo `pt_core_news_lg` é grande (cerca de 500 MB). Para usar outro modelo do spaCy, defina a variável `SPACY_MODEL` antes de subir a API, mas ele precisa ser compatível com o que foi usado no treino.

## Executando

### 1. API

Ainda em `projeto/`, com o ambiente virtual ativo:

```bash
uvicorn app.main:app --port 7860 --reload
```

O `--reload` reinicia o servidor quando você edita um arquivo. A primeira subida demora, porque carrega o spaCy e o modelo.

Teste rápido:

```bash
curl http://localhost:7860/api/health
```

Deve responder `{"ok":true}`. Documentação interativa da API: <http://localhost:7860/docs>.

Para testar a verificação direto, sem o site (PowerShell):

```powershell
curl.exe -X POST http://localhost:7860/api/verificar -H "Content-Type: application/json" -d "{\"sentenca\": \"A vacina reduziu as internações em 85%.\"}"
```

A resposta deve ser um JSON com `tipo`, `alertas`, `perguntas` e `fontes`.

### 2. Front-end

Em outro terminal, dentro de `projeto/frontend/`:

```bash
python -m http.server 8000
```

Abra <http://localhost:8000>. Cole um texto (ou use "Usar texto de exemplo"), clique em **Analisar Texto** e depois em uma frase sublinhada.

Abrir o `index.html` direto no navegador também costuma funcionar, porque a API libera CORS, mas servir por HTTP é mais confiável.

## Configuração

| Item | Onde | Observação |
|---|---|---|
| Porta da API | comando `uvicorn ... --port` e `fetch` em `frontend/script.js` | Os dois precisam coincidir (padrão: 7860) |
| Modelo do spaCy | variável de ambiente `SPACY_MODEL` | Padrão: `pt_core_news_lg` |
| Origens permitidas (CORS) | `allow_origins` em `app/main.py` | Está `"*"`; em produção, troque pelo domínio do front |
| Quantidade de fontes | `max_fontes` em `criticidade.py` e `max_results` em `main.py` | Padrão: busca 8, mostra 5 |

Não é necessária nenhuma chave de API.

## Instagram

O link de post ou reel é lido com a biblioteca `instaloader`, sem login. O Instagram bloqueia esse acesso com frequência. Se falhar, o sistema avisa para colar o texto da legenda no campo de texto.

## Problemas comuns

- **Erro mencionando "gemini" ou "modelo" no cartão**: o servidor ainda está rodando o `main.py` antigo. Pare o processo na porta 7860 e suba de novo com o arquivo novo.
- **`ModuleNotFoundError` ou `attempted relative import`**: rode `uvicorn app.main:app` a partir da pasta `projeto/`, não de dentro de `app/`, e confirme que existe `app/__init__.py`.
- **`OSError: [E050] Can't find model 'pt_core_news_lg'`**: rode `python -m spacy download pt_core_news_lg` com o ambiente virtual ativo.
- **`FileNotFoundError` do `.pkl`**: o arquivo precisa estar em `projeto/`, uma pasta acima de `app/`.
- **"Não foi possível conectar à API" no site**: a API não está de pé, ou a porta é outra. Confira o `fetch` em `script.js`.
- **"Falha ao pesquisar na internet"**: o DuckDuckGo pode limitar requisições. Espere alguns segundos e tente de novo.
- **Porta 7860 ocupada (PowerShell)**: `Get-NetTCPConnection -LocalPort 7860 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`

## Publicação (resumo)

1. Hospede a API (por exemplo, em um serviço que rode `uvicorn`) e inclua o `.pkl` e o modelo do spaCy no ambiente.
2. Em `frontend/script.js`, troque `http://localhost:7860` pela URL da API (há dois `fetch`).
3. Em `app/main.py`, troque `allow_origins=["*"]` pelo domínio onde o front ficará.
4. Publique a pasta `frontend/` em qualquer hospedagem estática.

## Limitações

As regras de `criticidade.py` (expressões regulares, limiar de 25% de palavras em comum, lista de domínios primários) são decisões da equipe e não foram validadas empiricamente. O cartão compara a frase apenas com título e resumo dos resultados de busca, não com a página inteira. Mais detalhes e as referências científicas estão no documento `embasamento-detector-de-claims.docx`.
