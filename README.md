<div align="center">

<img src="screenshots/app-icon.png" alt="Ícone do AF Copilot" width="90" />

# AF Copilot

**Copiloto Farmacêutico desktop para a Assistência Farmacêutica da SESAB/BA**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.1.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Electron](https://img.shields.io/badge/Electron-30-478BF9.svg)](https://www.electronjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg)](https://www.typescriptlang.org/)
[![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash%20Lite-4285F4.svg)](https://ai.google.dev/)

</div>

---

## 1. O que é o projeto

O **AF Copilot** é um **aplicativo desktop** (não é site, não é SaaS) que junta, em uma única janela:

- **à esquerda:** um clone funcional do portal AFSESAB, com 9 menus e 47 telas navegáveis, dados fictícios e ações reais sobre LMEs;
- **à direita:** uma sidebar de IA que responde perguntas em linguagem natural, analisa protocolos clínicos com RAG e valida receitas por visão computacional.

Tudo roda localmente. A chave da API fica somente no backend (`ai-backend/.env`, ignorado pelo Git). **Nenhum dado real de paciente é usado**: a base é sintética, com e-mails `@example.invalid` e nomes fictícios.

> **Repositório:** https://github.com/hensawa1/AF-Copilot
> **Relatório completo de entrega (PDF):** [`docs/Relatorio-Entrega-AF-Copilot.pdf`](docs/Relatorio-Entrega-AF-Copilot.pdf)

---

## 2. Prints do projeto

### Tela de login e aplicativo principal

| Login | Dashboard |
|-------|-----------|
| <img src="screenshots/01-login.png" alt="Login" width="420" /> | <img src="screenshots/02-dashboard.png" alt="Dashboard" width="420" /> |

### Portal e ações sobre LMEs

| Portal do AFSESAB (pacientes com Município/UF) | Tela de LMEs com ações |
|--------------------------------------------------|------------------------|
| <img src="screenshots/04-portal-pacientes.png" alt="Portal" width="420" /> | <img src="screenshots/03-lme-acoes.png" alt="LME" width="420" /> |

### Inteligência artificial

| Perguntar à IA | RAG — contexto sanitizado (sem CPF) |
|----------------|-------------------------------------|
| <img src="screenshots/05-ia-perguntar.png" alt="IA" width="420" /> | <img src="screenshots/06-rag-contexto-lgpd.png" alt="RAG LGPD" width="420" /> |

| RAG — critérios e exames | Validador de receita |
|--------------------------|----------------------|
| <img src="screenshots/07-rag-criterios.png" alt="RAG critérios" width="420" /> | <img src="screenshots/09-validador-receita.png" alt="Validador" width="420" /> |

### Segurança

| Auditoria no aplicativo | Perfil sem permissão (Assistente) |
|-------------------------|-----------------------------------|
| <img src="screenshots/08-auditoria.png" alt="Auditoria" width="420" /> | <img src="screenshots/10-perfil-assistente-negado.png" alt="RBAC" width="420" /> |

Os prints completos de todas as etapas estão em [`evidencias/`](evidencias/) e as saídas de testes em [`docs/evidencias/`](docs/evidencias/).

---

## 3. Tecnologias utilizadas

| Camada | Tecnologia | Função no projeto |
|--------|-----------|-------------------|
| Desktop | **Electron 30** + **TypeScript 5.5** | Janela split-view, BrowserView do portal, preload REA, IPC seguro e empacotamento. |
| Interface | HTML/CSS + renderer em TypeScript | Sidebar, tabelas, gráficos, botões de ação e estados de carregamento. |
| Backend | **FastAPI** (Python 3.11) | API REST, autenticação, RBAC, auditoria, validação de uploads e CORS restrito. |
| ORM / BD | **SQLAlchemy** + **SQLite** | Base sintética com 12.000 pacientes e 18.000 LMEs, índices e integridade verificada. |
| IA | **Gemini 3.5 Flash Lite** (fallbacks 3.1/3.8) | Interpreta perguntas, redige respostas, gera insights e faz OCR multimodal de receitas. |
| RAG | **LangChain** + **ChromaDB** + embeddings locais | Indexa PCDTs e recupera trechos para responder protocolos clinicamente. |
| Segurança | PBKDF2, tokens de sessão, PromptGuard, rate limit | Senha hasheada, sessão de 8 h, bloqueio de prompt injection e limites de login. |
| PDFs | **ReportLab** | Laudos de LME e o relatório de entrega. |
| Testes | **pytest**, **httpx**, **Playwright/CDP** | Testes automatizados, testes HTTP de segurança e captura das evidências visuais. |
| CI | **GitHub Actions** | Executa pytest e build a cada push. |

---

## 4. Como funciona

### 4.1 Arquitetura geral

```
[Clone AFSESAB] --(preload REA / MutationObserver)--> Electron Main
        | ipc: rea:context-raw
        v
[Sanitizador LGPD] -- remove CPF/CNS/e-mail/telefone --> ipc: rea:context
        v
[Sidebar renderer] -- token interno + sessão --> FastAPI (127.0.0.1:8000)
        v
[SQLite + RAG ChromaDB] --> resumo agregado --> Gemini redige --> resposta na tela
```

### 4.2 Fluxo RAG (ponta a ponta)

1. O usuário interage com um campo no portal (por exemplo: `metformina 850 mg E11 diabetes`).
2. O **REA** no preload captura o contexto e envia ao processo Main.
3. O **sanitizador LGPD** remove dados pessoais antes de qualquer envio — o print `06-rag-contexto-lgpd.png` mostra o `safeText` sem o CPF digitado.
4. A sidebar chama `POST /api/v1/analyze-context`.
5. O backend cruza os termos com a base de protocolos (base local instantânea + ChromaDB/Gemini) e devolve critérios, exames, alertas, fontes, passos e exemplo.
6. Tudo é gravado na auditoria com **quem pediu, o que foi consultado e quando**.

### 4.3 Copiloto de perguntas (`Perguntar à IA`)

Versão atual dos prompts: **v3**. O Gemini faz duas chamadas:

1. **Planner:** interpreta a pergunta e devolve um JSON com `intent`, `cidade`, `termo`, `cid`, `todos` e `entidade`;
2. **Writer:** recebe apenas um resumo agregado (sem PII) e redige a resposta final em 1–3 frases.

Exemplos reais:

- `Qual o fornecedor de Salvador?` → CNPJ, razão social, contato e endereço;
- `Quantos pacientes existem em Salvador?` → **2.929**;
- `Quais LMEs estão pendentes em Feira de Santana?` → **533**;
- `Quantos pacientes em Vitória da Conquista?` → **1.541**;
- `Quantos remédios existem?` → **40 medicamentos**.

Se o Gemini falhar ou atingir cota, o backend tenta os fallbacks e, se nenhum responder, usa uma resposta local determinística — o campo `model` da resposta informa honestamente o que aconteceu.

### 4.4 Perfis e permissões (RBAC)

| Perfil | O que pode fazer |
|--------|------------------|
| **Administrador** | Tudo: cadastro, LMEs, auditoria, exportação e IA. |
| **Farmacêutico** | Consultar pacientes/LMEs, ações em LME, validar receitas, RAG e insights. Não exporta auditoria. |
| **Auditor** | Somente leitura de auditoria, pacientes e IA. Não cadastra nem altera LMEs. |
| **Assistente** | Apenas consultas agregadas/genéricas. Não vê pacientes, validador, protocolos nem contexto; a IA devolve **0 linhas** e aviso de RBAC. |

A política é aplicada em quatro camadas: renderer (seções ocultas), IPC do Electron (`exigirPerfilClinico`), API (`require_perfil`) e IA (bloqueio de intenções com dados de pacientes). O equivalente em SQL está em [`ai-backend/scripts/rbac.sql`](ai-backend/scripts/rbac.sql) e [`docs/rbac_postgres.sql`](docs/rbac_postgres.sql).

### 4.5 Auditoria e segurança de dados

- Cada consulta à IA grava `ator`, `ação`, `entidade`, `detalhes` e `created_at` em `audit_logs` (append-only).
- O RAG grava fármacos, CID e fonte consultada; o validador grava status e fármacos.
- **Mascaramento/redação:** CPF, CNS, e-mail, telefone e nomes são removidos antes do LLM e dos logs.
- **PromptGuard:** bloqueia 12 padrões de prompt injection em português e inglês.
- **Login:** senha PBKDF2 (210.000 iterações), sessão de 8 h e rate limit (8 falhas/5 min por conta, 30/5 min por IP).
- **Headers:** `nosniff`, `X-Frame-Options: DENY`, `no-referrer`, `no-store`.

---

## 5. Estrutura do repositório

```
AF/
├── desktop-client/       # Electron + TypeScript (renderer, main, preload, clone do portal)
├── ai-backend/           # FastAPI, serviços de IA, seed, scripts e evidências em texto
├── docs/                 # PDF de entrega, prompts, workflow n8n, RBAC SQL e logs
├── evidencias/           # Prints reais de cada etapa
├── screenshots/          # Imagens usadas neste README
├── tools/                # Scripts Playwright/CDP de captura e calibração
├── datasets/             # Dataset de calibração/fine-tuning (ai-backend/datasets)
├── .github/workflows/    # CI
└── README.md
```

> Arquivos locais de execução (`smoke-test.ps1`, `start.ps1`, `TECNOLOGIAS.txt`, `VALIDATION.md`), `.env`, banco, `.venv`, `node_modules`, `runtime/` e `release/` **não são versionados**.

---

## 6. Como executar

### Pré-requisitos

- Python 3.11 (ou 3.12) e Node.js 20+
- Chave de API do Google Gemini (opcional — sem ela o app usa fallback local)

### 6.1 Backend

```powershell
cd ai-backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
# edite .env e coloque GEMINI_API_KEY=sua-chave
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Saúde do serviço: `http://127.0.0.1:8000/health`.

### 6.2 Aplicativo desktop

```powershell
cd desktop-client
npm install
npm run dev          # compila e abre o Electron
```

Para gerar o executável:

```powershell
npm run build
npm run package
```

O instalador/executável aparece em `desktop-client/release/AF Copilot/`. O atalho na Área de Trabalho usa `--demo` (somente dados fictícios).

### 6.3 Testes

```powershell
cd ai-backend
.\.venv\Scripts\python -m pytest tests -q
.\.venv\Scripts\python security_test.py
.\.venv\Scripts\python rbac_evidence.py
```

---

## 7. Evidências e relatório

- **Relatório final (PDF):** [`docs/Relatorio-Entrega-AF-Copilot.pdf`](docs/Relatorio-Entrega-AF-Copilot.pdf)
- **Prompts versionados:** [`docs/PROMPTS.md`](docs/PROMPTS.md)
- **Fluxo n8n importável:** [`docs/n8n-workflow.json`](docs/n8n-workflow.json)
- **Planos de execução:** [`docs/planos-execucao.txt`](docs/planos-execucao.txt)
- **RBAC em SQL:** [`docs/rbac_postgres.sql`](docs/rbac_postgres.sql)
- **Saídas de testes:** [`docs/evidencias/`](docs/evidencias/)
- **Prints:** [`evidencias/`](evidencias/)

### Resultados medidos

- `pytest`: **5 testes passando**
- Teste de segurança: **16/20 requisições**, todos os testes aprovados (SQLi, prompt injection, rate limit e headers)
- RBAC: Admin `200/200/200` e 100 linhas via IA; Assistente `403/403/403` e **0 linhas** via IA
- Latência Gemini 3.5 Flash Lite: **10.217 ms** (fria), **1.305 ms** (aquecida), **~7 ms** em cache
- Volume: 12.000 pacientes, 18.000 LMEs, 40 medicamentos, 8 unidades e 6 fornecedores
- Fine-tuning local (GPT-2 português): loss de validação **6,3510 → 4,7589** (perplexidade 573 → 117)

---

## 8. Limitações declaradas

- **n8n:** não foi instalada uma instância no ambiente; o fluxo real roda no backend e o workflow importável está em `docs/n8n-workflow.json`.
- **Fine-tuning do Gemini:** a chave disponível não expõe treino supervisionado; por isso foi executado um fine-tuning **local real** com GPT-2 português, mantendo o Gemini em produção.
- **Cota free-tier:** pode retornar 429; o fallback automático e o cache reduzem o impacto.
- **MongoDB:** auditoria/cache distribuídos ficam para a Fase 2 (stub já preparado).

---

## 9. Identificação do grupo

Preencha antes da entrega:

- **Grupo:** `[PREENCHER]`
- **Integrantes (nome — matrícula):** `[PREENCHER]`
- **Disciplinas cursadas:** `[PREENCHER]`

---

Projeto desenvolvido para fins acadêmicos. Uso de dados exclusivamente fictícios e anonimizados.
