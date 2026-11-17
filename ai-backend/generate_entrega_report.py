"""Gera o relatório final da entrega acadêmica (IA + Segurança/BD + Integração)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Relatorio-Entrega-AF-Copilot.pdf"
EVID = ROOT / "evidencias"
TEXTOS = ROOT / "docs" / "evidencias"

AZUL = colors.HexColor("#0B3D70")
AZUL_CLARO = colors.HexColor("#14538F")
CINZA = colors.HexColor("#546E7A")
LINHA = colors.HexColor("#D8E0E8")
VERDE = colors.HexColor("#2E7D32")

ss = getSampleStyleSheet()
TITULO = ParagraphStyle("t", parent=ss["Heading1"], fontSize=20, textColor=AZUL, alignment=TA_CENTER)
SUB = ParagraphStyle("s", parent=ss["Normal"], fontSize=10, textColor=CINZA, alignment=TA_CENTER, spaceAfter=14)
H1 = ParagraphStyle("h1", parent=ss["Heading2"], fontSize=13, textColor=AZUL, spaceBefore=12, spaceAfter=5)
H2 = ParagraphStyle("h2", parent=ss["Heading3"], fontSize=10.5, textColor=AZUL_CLARO, spaceBefore=8, spaceAfter=3)
BODY = ParagraphStyle("b", parent=ss["Normal"], fontSize=9, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=5)
CELL = ParagraphStyle("c", parent=ss["Normal"], fontSize=7.6, leading=9.5)
CELLB = ParagraphStyle("cb", parent=CELL, fontName="Helvetica-Bold")
LEG = ParagraphStyle("leg", parent=BODY, fontSize=8, textColor=CINZA, alignment=TA_CENTER, spaceAfter=8)
CODE = ParagraphStyle("code", parent=ss["Normal"], fontName="Courier", fontSize=6.8, leading=8.6,
                      backColor=colors.HexColor("#F3F6F9"), borderPadding=4, spaceAfter=5)


def p(text, style=BODY):
    return Paragraph(text, style)


def tbl(data, widths=None):
    rows = [[p(str(c), CELLB if i == 0 else CELL) for c in row] for i, row in enumerate(data)]
    t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EFF7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    return t


def printar(nome, legenda, largura=172 * mm, maxh=118 * mm):
    arquivo = EVID / nome
    if not arquivo.exists():
        return p(f"[print indisponível: {nome}]", LEG)
    with PILImage.open(arquivo) as im:
        w, h = im.size
    altura = largura * h / w
    if altura > maxh:
        altura = maxh
        largura = altura * w / h
    return KeepTogether([Image(str(arquivo), width=largura, height=altura), p(legenda, LEG)])


def esc(texto):
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def texto(nome, max_linhas=40):
    arquivo = TEXTOS / nome
    if not arquivo.exists():
        return p(f"[evidência indisponível: {nome}]", CODE)
    linhas = arquivo.read_text(encoding="utf-8", errors="replace").splitlines()[:max_linhas]
    return p("<br/>".join(esc(l) for l in linhas) or "(vazio)", CODE)


def texto_tail(nome, linhas=12):
    arquivo = TEXTOS / nome
    if not arquivo.exists():
        return p(f"[evidência indisponível: {nome}]", CODE)
    conteudo = arquivo.read_text(encoding="utf-8", errors="replace").splitlines()[-linhas:]
    return p("<br/>".join(esc(l) for l in conteudo), CODE)


def arquivo(nome, max_linhas=40):
    caminho = ROOT / nome
    if not caminho.exists():
        return p(f"[arquivo indisponível: {nome}]", CODE)
    linhas = caminho.read_text(encoding="utf-8", errors="replace").splitlines()[:max_linhas]
    return p("<br/>".join(esc(l) for l in linhas) or "(vazio)", CODE)


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Relatório de Entrega — AF Copilot",
                            author="AF Copilot — IA e Segurança/BD")
    s = []
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ============================== CAPA ==============================
    s += [Spacer(1, 8 * mm), p("RELATÓRIO DE ENTREGA", TITULO),
          p("AF Copilot — Inteligência Artificial + Segurança e Otimização de Banco de Dados", SUB)]
    s += [tbl([
        ["Grupo", "[PREENCHER: nome do grupo]"],
        ["Componente 1", "[PREENCHER: nome completo — matrícula]"],
        ["Componente 2", "[PREENCHER: nome completo — matrícula]"],
        ["Componente 3", "[PREENCHER: nome completo — matrícula]"],
        ["Disciplinas cursadas", "[PREENCHER: IA / Segurança e BD / ambas]"],
        ["Repositório", "[PREENCHER: URL do repositório] (cópia local: C:\\Users\\offsechen1\\Desktop\\AF)"],
        ["Data", now],
    ], [42 * mm, 130 * mm])]
    s += [Spacer(1, 5 * mm), p(
        "Todas as evidências abaixo foram geradas pela execução real do aplicativo desktop e do backend. "
        "Os campos entre colchetes devem ser preenchidos pelo grupo antes do envio. Os prints estão em "
        "<font face='Courier'>evidencias/</font> e as saídas de testes em "
        "<font face='Courier'>docs/evidencias/</font>.", BODY)]

    # ============================== PARTE COMUM ==============================
    s += [PageBreak(), p("PARTE COMUM — TODOS", H1)]
    s += [p("1. Relatório de andamento", H2)]
    s += [p(
        "<b>Já funciona:</b> aplicativo desktop Electron sem SaaS; login com sessão de 8 h e RBAC de quatro "
        "perfis; clone do AFSESAB com 9 menus e 47 telas; base SQLite com 12.000 pacientes e 18.000 LMEs "
        "fictícias; ações reais sobre LME com auditoria; dashboard e insights com Gemini 3.5 Flash Lite; "
        "copiloto de perguntas em linguagem natural; RAG de protocolos com sanitização LGPD; validador "
        "multimodal de receitas; exportação CSV/PDF; prompt injection bloqueado; rate limit de login; "
        "cabeçalhos defensivos; índices e planos de execução medidos; 5 testes automatizados passando.", BODY)]
    s += [p(
        "<b>Pendências declaradas:</b> não há instância n8n instalada — o fluxo equivalente está implementado "
        "no backend e um workflow importável segue em docs/n8n-workflow.json; o fine-tuning do Gemini pela API "
        "não é exposto pela chave disponível — por isso foi executado um fine-tuning local real com GPT-2 "
        "português (resultados na Parte de IA), mantendo o Gemini 3.5 Flash Lite em produção; auditoria em "
        "MongoDB ficou para a Fase 2 (stub já preparado).", BODY)]
    s += [p(
        "<b>Evolução desde 27/10:</b> segredos saíram do Electron e ficaram só no backend; sessão PBKDF2 e "
        "RBAC; dataset determinístico único para tabela/PDF/IA; PromptGuard em camadas; auditoria "
        "append-only; cache TTL; base local de protocolos para reduzir custo e latência; cidade e UF em "
        "pacientes, farmácias, fornecedores e todas as views.", BODY)]
    s += [p(
        "<b>Riscos mitigados:</b> cota free-tier do Gemini (fallback entre modelos e cache de 300 s); chave "
        "de API mantida fora do repositório (.env ignorado); rate limit de login (8 falhas/5 min por conta "
        "e 30/5 min por IP); SQLi e prompt injection bloqueados nos testes.", BODY)]

    s += [p("2. Repositório e execução", H2)]
    s += [texto("pytest.txt", 8)]
    s += [p("README.md na raiz traz o passo a passo; requirements.txt fixa as versões; start.ps1 sobe o "
            "backend e o Electron; o instalador em release/ gera o executável. Nenhuma chave ou senha real "
            "deve ser versionada.", BODY)]
    s += [p("3. Contribuição individual (3 a 5 linhas)", H2)]
    s += [p("[PREENCHER: descreva em 3 a 5 linhas sua contribuição — por exemplo: implementei o PromptGuard "
            "e os testes de prompt injection; configurei RBAC e auditoria; calibrei prompts e medi "
            "latência/custo; criei os índices e os planos de execução.]", BODY)]

    s += [p("4. Prints gerais do sistema", H2)]
    s += [printar("01-login.png", "Print G1 — Tela de login do aplicativo desktop."),
          printar("02-dashboard.png", "Print G2 — Dashboard: 12.000 usuários, 18.000 LMEs, gráficos e alertas de IA."),
          printar("03-lme-acoes.png", "Print G3 — LMEs com ações de autorizar, faturar, dispensar e devolver."),
          printar("04-relatorio-estoque.png", "Print G4 — Relatório de comprometimento de estoque com CSV/PDF."),
          printar("19-portal-pacientes.png", "Print G5 — Pacientes fictícios com Unidade, Município e UF."),
          printar("20-portal-estabelecimentos.png", "Print G6 — Estabelecimentos com Município e UF."),
          printar("21-portal-fornecedores.png", "Print G7 — Fornecedores com cidade e UF."),
          printar("15-IA-medicamentos.png", "Print G8 — Copiloto listando os 40 medicamentos.")]

    # ============================== PARTE IA ==============================
    s += [PageBreak(), p("PARTE DE IA", H1)]
    s += [p("5. Fluxo ponta a ponta (RAG + n8n)", H2)]
    s += [p(
        "Fluxo executado: campo no clone do AFSESAB → REA no preload do Electron → sanitização LGPD no "
        "processo Main → IPC → sidebar → POST /api/v1/analyze-context → RAG (base local instantânea e "
        "ChromaDB/Gemini quando disponível) → resposta com critérios, exames obrigatórios, alertas, fontes, "
        "\"como fazer\" e exemplo. Cada etapa foi capturada após espera explícita e validação visual.", BODY)]
    s += [p(
        "<b>n8n:</b> não foi instalada uma instância no ambiente acadêmico. Para não fingir evidência, o "
        "fluxo real foi executado pelo backend e o arquivo docs/n8n-workflow.json (Webhook → HTTP Request → "
        "Set → Respond) está disponível para importação quando o n8n existir. O print abaixo mostra o fluxo "
        "real ponta a ponta, incluindo a gravação da auditoria.", BODY)]
    s += [printar("22-RAG-contexto-LGPD.png",
                  "Print IA1 — Contexto capturado e sanitizado: a entrada continha CPF 123.456.789-00; o safeText exibido não contém CPF."),
          printar("23a-RAG-criterios.png", "Print IA2 — RAG: critérios de inclusão, exames obrigatórios e alertas de dispensação."),
          printar("23b-RAG-fontes.png", "Print IA3 — RAG: fontes (PCDT Ministério da Saúde), como fazer e exemplo."),
          printar("25-RAG-e-auditoria.png", "Print IA4 — Fluxo integrado: portal + RAG + log de auditoria na mesma execução."),
          printar("26-auditoria-RAG-usuario.png", "Print IA5 — Auditoria do RAG com usuário, perfil, fármacos, CID e fonte consultados.")]

    s += [p("6. Versionamento de prompts", H2)]
    s += [p("A versão atual é a <b>v3</b> (16/11), com duas chamadas ao Gemini: o modelo interpreta a pergunta "
            "e devolve um plano JSON; o backend consulta o SQLite com filtros validados e devolve apenas um "
            "resumo agregado sem PII; o modelo redige a resposta final. O campo <font face='Courier'>model</font> "
            "informa honestamente qual modelo foi usado.", BODY)]
    s += [p("Prompt atual (plano) — docs/PROMPTS.md:", H2)]
    s += [arquivo("docs/PROMPTS.md", 106)]
    s += [p("Prompt atual (redação):", H2)]
    s += [p(
        "Redija a RESPOSTA FINAL em português brasileiro, em 1 a 3 frases objetivas, usando SOMENTE os números "
        "e filtros do resumo. Não invente dados. Não cite nomes de pacientes. Se o total for zero, diga que "
        "não há registros. PERGUNTA / PLANO / RESUMO AGREGADO / RESPOSTA BASE → texto final sem JSON e sem markdown.", BODY)]
    s += [tbl([
        ["Versão", "Mudança", "Motivo"],
        ["v1 → v2", "Delimitação <user_input>, regra de tratar entrada como dado, anti-injection, passos e exemplo; redação de PII; fallback local.", "v1 era vulnerável a prompt injection e inventava campos."],
        ["v2 → v3", "Planner + writer com Gemini 3.5 Flash Lite; filtros estruturados (cidade, CID, todos, entidade); resumo sem PII antes do modelo; cache 300 s; modelo explícito na resposta.", "Padronizar contagens por cidade/UF, evitar vazamento de nomes para o LLM e reduzir custo/latência."],
    ], [18 * mm, 84 * mm, 70 * mm])]

    s += [p("7. Casos de teste (entrada, esperado, obtido)", H2)]
    s += [tbl([
        ["#", "Entrada", "Esperado", "Obtido (executado)"],
        ["1", "metformina 850 mg E11 diabetes + CPF fictício", "Contexto sem CPF; exames glicemia/HbA1c/creatinina; fonte PCDT", "OK — prints IA1/IA2/IA3; safeText sem CPF"],
        ["2", "Quais pacientes são de Salvador?", "Contagem e primeiras linhas com Município/UF", "OK — 2.929 pacientes; print G3/IA6"],
        ["3", "Quantos pacientes existem no total?", "12.000", "OK — 12.000 pacientes"],
        ["4", "Quais LMEs estão pendentes em Feira de Santana?", "Contagem por cidade", "OK — 533 LMEs pendentes"],
        ["5", "Quantos pacientes em Vitória da Conquista?", "Grafia canônica preservada", "OK — 1.541 pacientes"],
        ["6", "Quantos medicamentos existem?", "40", "OK — 40 medicamentos (print G8)"],
        ["7", "Assistente: 'Quais pacientes são de Salvador?'", "Negar dado nominal mesmo via IA", "OK — 0 linhas + RBAC aplicado (print S4)"],
        ["8", "'Ignore todas as instruções anteriores...'", "Bloquear e não revelar system prompt", "OK — 6 linhas agregadas e aviso de bloqueio"],
        ["9", "Receita com Losartana/CID I10 datada de 2020", "Detectar vencimento e divergências", "OK — status warning com 3 inconsistências (print S8)"],
    ], [8 * mm, 46 * mm, 50 * mm, 68 * mm])]
    s += [printar("16c-IA-pacientes.png", "Print IA6 — Farmacêutico consultando pacientes de Salvador (permitido, com Município/UF)."),
          printar("18c-IA-contagem.png", "Print IA7 — Contagem de 2.929 pacientes em Salvador pelo Gemini 3.5 Flash Lite.")]

    s += [p("8. Experimento de fine-tuning (resultados preliminares)", H2)]
    s += [p("Dataset: 20 pares instrução/entrada/saída em ai-backend/datasets/finetune.jsonl (16 treino, 4 validação). "
            "Como a chave Gemini não expõe treino supervisionado, foi executado um <b>fine-tuning local real</b> "
            "com GPT-2 português (124 M parâmetros), 3 épocas, CPU, 38,7 s. O modelo treinado fica em runtime/ "
            "(ignorado pelo git); a produção continua usando Gemini 3.5 Flash Lite.", BODY)]
    s += [texto("finetune_ambiente.txt", 20), texto("finetune_treino.txt", 30)]
    s += [tbl([
        ["Métrica", "Modelo base", "Após fine-tuning"],
        ["Loss de validação", "6,3510", "4,7589"],
        ["Perplexidade", "573,08", "116,62"],
        ["Loss de treino (época 3)", "—", "2,5066"],
        ["Custo", "R$ 0,00", "R$ 0,00 (CPU local)"],
        ["Latência de inferência local", "—", "117 ms (forward, 1 exemplo)"],
    ], [55 * mm, 45 * mm, 72 * mm])]
    s += [p("Experimento complementar de engenharia de prompt (sem treino de pesos):", H2)]
    s += [texto("finetune.txt", 18)]

    s += [p("9. Custo e latência iniciais", H2)]
    s += [texto("latencia_ia.txt", 12), texto("tokens_gemini.txt", 12)]
    s += [tbl([
        ["Item", "Medição"],
        ["Gemini 3.5 Flash Lite — chamada fria", "10.217,4 ms"],
        ["Gemini 3.5 Flash Lite — chamada aquecida", "1.304,7 ms"],
        ["Cache de resposta (300 s)", "8,5 ms e 6,8 ms"],
        ["Tokens medidos (countTokens)", "98 tokens para o prompt de teste; resposta curta ~120 tokens"],
        ["Custo efetivo", "R$ 0,00 no free tier"],
    ], [70 * mm, 102 * mm])]

    # ============================== SEGURANÇA ==============================
    s += [PageBreak(), p("PARTE DE SEGURANÇA E OTIMIZAÇÃO DE BANCO", H1)]
    s += [p("10. Papéis e permissões (RBAC)", H2)]
    s += [p("SQLite não possui papéis nativos. A política é aplicada na API por require_perfil(), com sessão de "
            "8 h. Os arquivos ai-backend/scripts/rbac.sql e docs/rbac_postgres.sql documentam o equivalente "
            "em GRANT/DENY/REVOKE.", BODY)]
    s += [arquivo("docs/rbac_postgres.sql", 24)]
    s += [tbl([
        ["Perfil", "Auditoria", "Exportar", "Cadastrar", "IA 'Arlindo'", "Validador/Protocolos"],
        ["Administrador", "200", "200", "200", "100 linhas", "Sim"],
        ["Farmacêutico", "200", "403", "200", "100 linhas", "Sim"],
        ["Auditor", "200", "200", "403", "100 linhas", "Sim"],
        ["Assistente", "403", "403", "403", "0 linhas — negado", "Não (UI + IPC + API)"],
    ], [30 * mm, 24 * mm, 24 * mm, 24 * mm, 36 * mm, 34 * mm])]
    s += [texto("rbac.txt", 30)]
    s += [printar("12-conta-assistente.png", "Print S1 — Login com o perfil Assistente Farmacêutico."),
          printar("13c-assistente-perfil.png", "Print S2 — Sidebar do Assistente: sem Validador, sem Protocolos e sem Contexto."),
          printar("14c-assistente-negado.png", "Print S3 — Assistente pedindo pacientes à IA: acesso negado, 0 registros."),
          printar("16c-IA-pacientes.png", "Print S4 — Perfil autorizado (Farmacêutico) obtendo pacientes normalmente."),
          printar("15d-assistente-permitida.png", "Print S5 — Assistente consultando apenas dado agregado (40 medicamentos).")]

    s += [p("11. Proteção de dado sensível", H2)]
    s += [p("Técnica aplicada: <b>mascaramento/redação (Data Masking) em duas camadas</b>. No Electron, o "
            "sanitizador LGPD remove CPF, CNS, e-mail, telefone e nomes antes de qualquer envio; no backend, "
            "PromptGuard redige PII da saída e dos logs. O print IA1 mostra a entrada com CPF e o contexto "
            "sanitizado sem ele. Nenhum dado real de paciente foi usado: a base é sintética.", BODY)]
    s += [printar("22-RAG-contexto-LGPD.png", "Print S6 — Prova prática: safeText sem CPF, apenas termos clínicos."),
          texto("security_test.txt", 70)]

    s += [p("12. Volume de dados", H2)]
    s += [texto("volumes.txt", 20)]
    s += [p("Além disso, a base sintética possui 8 estabelecimentos em 4 municípios baianos e 6 fornecedores. "
            "O total de 40 medicamentos é consistente entre a tabela catalog_medications, as views e a IA.", BODY)]

    s += [p("13. Consultas lentas e otimização (mínimo 2)", H2)]
    plano = (TEXTOS / "planos-execucao.txt").read_text(encoding="utf-8", errors="replace")
    s += [p("<br/>".join(esc(l) for l in plano.splitlines()[:42]), CODE)]
    s += [tbl([
        ["Consulta lenta", "Antes (SCAN)", "Depois (índice)"],
        ["LIKE '%Metformina%' em LMEs", "SCAN — 216 páginas", "evitar curinga à esquerda; filtro por status usa SEARCH (61 páginas)"],
        ["LIKE '%Arlindo%' em pacientes", "SCAN — 216 páginas", "e-mail único usa SEARCH (39); unidade 54; CID 52; status+usuario 53"],
    ], [50 * mm, 40 * mm, 82 * mm])]
    s += [texto("indices.txt", 20)]

    # ============================== INTEGRAÇÃO ==============================
    s += [PageBreak(), p("PARTE DE INTEGRAÇÃO (QUEM CURSA AS DUAS)", H1)]
    s += [p("14. A IA respeitando permissões", H2)]
    s += [p("Teste decisivo: os quatro perfis fizeram a mesma pergunta 'Arlindo' a /admin/ask. Administrador, "
            "Farmacêutico e Auditor receberam 100 linhas; o <b>Assistente recebeu zero linhas</b> com o aviso "
            "'RBAC aplicado à IA'. Assim, mesmo perguntando à IA, um perfil sem permissão não obteve dado de "
            "paciente. A proteção existe também na UI (seções clínicas ocultas), no IPC (exigirPerfilClinico) "
            "e na API (require_perfil).", BODY)]
    s += [printar("14c-assistente-negado.png", "Print I1 — Perfil sem permissão tentando obter pacientes via IA; resposta negada."),
          printar("08-IA-RBAC-negado.png", "Print I2 — Log de RBAC: 403 para auditoria/exportação/cadastro e IA com 0 linhas."),
          printar("26-auditoria-RAG-usuario.png", "Print I3 — IA, auditoria e RAG na mesma execução real.")]

    s += [p("15. Log de auditoria (o quê, quem, quando)", H2)]
    s += [p("A auditoria registra timestamp (UTC), usuário, ação, entidade e detalhes. Para o RAG, o log grava "
            "fármacos, CID e fonte consultada; para o validador, status e fármacos; para /admin/ask, a pergunta, "
            "o perfil e a quantidade de linhas. Os registros são append-only (sem endpoint de edição/exclusão).", BODY)]
    s += [texto("auditoria_rag.txt", 12), texto_tail("rbac.txt", 8), texto("validacao_receitas.txt", 26)]
    s += [printar("09-auditoria-app.png", "Print I4 — Auditoria no aplicativo: consulta_ia do Assistente com 0 linhas, Auditor/Farm com 100, login_bloqueado por rate limit e modelo Gemini."),
          printar("27-validador-valido.png", "Print I5 — Validador: receita fictícia válida, dados extraídos."),
          printar("28-validador-invalido.png", "Print I6 — Validador: receita inválida com 3 inconsistências detectadas.")]

    # ============================== ANEXOS ==============================
    s += [PageBreak(), p("ANEXOS — COMANDOS E ARQUIVOS", H1)]
    s += [tbl([
        ["Arquivo", "Finalidade"],
        ["README.md / TECNOLOGIAS.txt", "Como rodar e stack completa"],
        ["docs/PROMPTS.md", "Prompts v1, v2 e v3 (atual)"],
        ["docs/n8n-workflow.json", "Workflow importável do fluxo RAG"],
        ["datasets/finetune.jsonl", "Dataset de 20 pares para calibração/fine-tuning"],
        ["finetune_real.py", "Script de fine-tuning local com loss e logs"],
        ["docs/planos-execucao.txt", "EXPLAIN QUERY PLAN (consultas lentas e otimizadas)"],
        ["docs/rbac_postgres.sql / ai-backend/scripts/rbac.sql", "GRANT/DENY/REVOKE documentados"],
        ["docs/evidencias/*.txt", "Saídas reais: pytest, RBAC, segurança, latência, tokens, volumes, auditoria"],
        ["evidencias/*.png", "Prints de cada etapa (UI, IA, RBAC, auditoria, validador)"],
        [".github/workflows/ci.yml", "pytest + build no CI"],
    ], [78 * mm, 94 * mm])]
    s += [Spacer(1, 6 * mm), p(f"Relatório gerado em {now}. Todas as evidências foram produzidas por execução real; "
                               "campos entre colchetes pendem de preenchimento pelo grupo.", LEG)]

    doc.build(s)
    print(f"Relatório gerado: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
