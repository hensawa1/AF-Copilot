"""Consultas em linguagem natural sobre a base do AF Copilot.

Fluxo (RAG de verdade):
1. O Gemini 3.5 Flash Lite INTERPRETA a pergunta e devolve um plano JSON
   (intenção + filtros: cidade, termo, CID, "todos").
2. O backend consulta o SQLite e monta os dados reais (tabela da resposta).
3. O Gemini REDIGE a resposta final a partir de um resumo AGREGADO — sem
   enviar nomes, CNS ou outros dados pessoais ao modelo (LGPD).

Se o modelo estiver sem cota, há um roteador local de contingência: a aplicação
continua respondendo e o campo ``model`` informa honestamente o que respondeu.
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.logging import get_logger
from ..core.territorio import uf_do_municipio
from ..models.sql_models import FictionalLme, FictionalUser
from .fictional_views import ESTABELECIMENTOS, FORNECEDORES, MEDICAMENTOS

logger = get_logger(__name__)
_JSON = re.compile(r"\{.*\}", re.DOTALL)
_CID = re.compile(r"\b([A-TV-Z]\d{2}(?:\.\d{1,4})?)\b")
_INTENTS = {
    "fornecedores", "medicamentos", "pacientes", "lmes-pendentes",
    "lmes-por-cid", "visao-geral", "contagem",
}


def _cidade_label(cidade: Any) -> str:
    """Preserva a grafia canônica (ex.: 'Vitória da Conquista') e corrige minúsculas."""
    if not cidade:
        return ""
    texto = str(cidade).strip()
    return texto[:1].upper() + texto[1:]


class AdminAskService:
    # Compartilhado entre instâncias: o endpoint cria um serviço por requisição.
    _models: dict[str, Any] = {}
    _cache: dict[str, tuple[float, dict[str, Any]]] = {}
    CACHE_TTL = 300

    # Unidade -> cidade, derivado de ESTABELECIMENTOS.
    UNIDADE_CIDADE = {nome: cidade for _, nome, cidade, _ in ESTABELECIMENTOS}
    CIDADES = sorted(
        {cidade for _, _, cidade, _ in ESTABELECIMENTOS}
        | {f[2] for f in FORNECEDORES}
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ------------------------------------------------------------------ #
    # 1) Gemini interpreta a pergunta
    # ------------------------------------------------------------------ #
    def _model(self, name: str) -> Any:
        if name not in self._models:
            from langchain_google_genai import ChatGoogleGenerativeAI

            self._models[name] = ChatGoogleGenerativeAI(
                model=name,
                google_api_key=self.settings.gemini_api_key,
                temperature=0.1,
                timeout=12,
                max_retries=0,
                transport="rest",
            )
        return self._models[name]

    def _invoke(self, name: str, prompt: str, timeout: int = 12) -> str:
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            future = pool.submit(self._model(name).invoke, prompt)
            content = future.result(timeout=timeout).content
            # Alguns modelos retornam lista de blocos; normaliza para texto.
            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if isinstance(item, dict):
                        parts.append(str(item.get("text", "")))
                    else:
                        parts.append(str(item))
                return "".join(parts)
            return str(content)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    def _plan(self, question: str) -> tuple[dict[str, Any], str]:
        prompt = f"""Você é o roteador de consultas do AF Copilot (SESAB).
Classifique a pergunta e extraia os filtros. Responda SOMENTE com JSON válido,
sem markdown, no formato:
{{"intent": "fornecedores|medicamentos|pacientes|lmes-pendentes|lmes-por-cid|visao-geral|contagem",
  "cidade": null, "termo": null, "cid": null, "todos": false, "entidade": null}}

Regras:
- fornecedores: perguntas sobre fornecedores, CNPJ, distribuidoras.
- medicamentos: lista/busca de medicamentos cadastrados.
- pacientes: perguntas sobre pacientes. Se citar cidade, preencha "cidade".
  Se citar um nome, preencha "termo". "todos os pacientes" -> todos=true.
- lmes-pendentes: LMEs não autorizadas, pendentes ou aguardando.
- lmes-por-cid: LMEs por CID (preencha "cid", ex.: E11).
- visao-geral: panorama, totais, indicadores gerais.
- contagem: "quantos/quantas ..." (preencha "entidade": pacientes, medicamentos,
  fornecedores ou lmes).
- "cidade" deve ser apenas o nome da cidade. Datas e números não entram em "termo".

Pergunta: {json.dumps(question, ensure_ascii=False)}"""
        models = [self.settings.gemini_model, *self.settings.gemini_fallback_models]
        for name in dict.fromkeys(models):
            if not self.settings.gemini_api_key:
                break
            try:
                parsed = self._parse(self._invoke(name, prompt))
                plan = self._normalize_plan(parsed, question)
                if plan:
                    logger.info("Plano da IA (%s): %s", name, plan)
                    return plan, name
            except Exception as exc:  # noqa: BLE001
                logger.warning("Modelo %s falhou ao interpretar a pergunta: %s", name, exc)
        return self._plan_local(question), "roteador-local"

    def _plan_local(self, question: str) -> dict[str, Any]:
        q = question.lower()
        city = next((c for c in self.CIDADES if c.lower() in q), None)
        cid_match = _CID.search(question.upper())
        plan: dict[str, Any] = {
            "intent": "visao-geral", "cidade": city, "termo": None,
            "cid": cid_match.group(1) if cid_match else None,
            "todos": "todos" in q, "entidade": None,
        }
        if "fornecedor" in q or "cnpj" in q or "distribuidora" in q:
            plan["intent"] = "fornecedores"
        elif "quantos" in q or "quantas" in q:
            plan["intent"] = "contagem"
            if "paciente" in q:
                plan["entidade"] = "pacientes"
            elif "medicamento" in q or "remédio" in q or "remedio" in q:
                plan["entidade"] = "medicamentos"
            elif "fornecedor" in q:
                plan["entidade"] = "fornecedores"
            elif "lme" in q:
                plan["entidade"] = "lmes"
        elif "lme" in q and any(w in q for w in (
            "não autorizada", "nao autorizada", "não foram autorizadas",
            "nao foram autorizadas", "sem autorização", "sem autorizacao",
            "pendente", "aguardando",
        )):
            plan["intent"] = "lmes-pendentes"
        elif "lme" in q and cid_match:
            plan["intent"] = "lmes-por-cid"
        elif "medicamento" in q or "remédio" in q or "remedio" in q:
            plan["intent"] = "medicamentos"
        elif "paciente" in q:
            plan["intent"] = "pacientes"
        return plan

    def _normalize_plan(self, parsed: dict[str, Any], question: str) -> dict[str, Any] | None:
        if not isinstance(parsed, dict):
            return None
        intent = str(parsed.get("intent", "")).strip().lower()
        if intent not in _INTENTS:
            return None
        city = parsed.get("cidade")
        if isinstance(city, str) and city.strip():
            match = next((c for c in self.CIDADES if c.lower() == city.strip().lower()), None)
            city = match or city.strip()[:60]
        else:
            city = None
        termo = parsed.get("termo")
        termo = str(termo).strip()[:60] if isinstance(termo, str) and str(termo).strip() else None
        cid = parsed.get("cid")
        if isinstance(cid, str) and _CID.fullmatch(cid.strip().upper()):
            cid = cid.strip().upper()
        else:
            match = _CID.search(question.upper())
            cid = match.group(1) if match else None
        entidade = parsed.get("entidade")
        entidade = str(entidade).strip().lower() if isinstance(entidade, str) else None
        return {
            "intent": intent,
            "cidade": city,
            "termo": termo,
            "cid": cid,
            "todos": bool(parsed.get("todos")),
            "entidade": entidade,
        }

    # ------------------------------------------------------------------ #
    # 2) Consulta real no SQLite (dados que aparecem na tabela)
    # ------------------------------------------------------------------ #
    def answer(self, question: str, db: Session) -> dict[str, Any]:
        key = " ".join(question.lower().split())
        cached = self._cache.get(key)
        if cached and time.time() - cached[0] < self.CACHE_TTL:
            logger.info("Consulta em cache: %s", key[:60])
            return cached[1]

        plan, planner = self._plan(question)
        result = self._retrieve(plan, db, question)
        result = self._draft(question, plan, result, planner)
        self._cache[key] = (time.time(), result)
        return result

    def _units_for_city(self, city: str | None) -> list[str]:
        if not city:
            return []
        return [u for u, c in self.UNIDADE_CIDADE.items() if c.lower() == city.lower()]

    def _user_query(self, db: Session, plan: dict[str, Any]):
        q = db.query(FictionalUser)
        units = self._units_for_city(plan.get("cidade"))
        if units:
            q = q.filter(FictionalUser.unidade.in_(units))
        elif plan.get("cidade"):
            # Cidade sem unidade mapeada: não inventa resultado.
            q = q.filter(func.lower(FictionalUser.unidade) == str(plan["cidade"]).lower())
        if plan.get("termo") and plan.get("intent") == "pacientes":
            q = q.filter(FictionalUser.nome.ilike(f"%{plan['termo']}%"))
        return q

    def _lme_query(self, db: Session, plan: dict[str, Any], status: str | None = None):
        q = db.query(FictionalLme).join(
            FictionalUser, FictionalLme.user_id == FictionalUser.id
        )
        units = self._units_for_city(plan.get("cidade"))
        if units:
            q = q.filter(FictionalUser.unidade.in_(units))
        elif plan.get("cidade"):
            q = q.filter(func.lower(FictionalUser.unidade) == str(plan["cidade"]).lower())
        if status:
            q = q.filter(FictionalLme.status == status)
        if plan.get("cid"):
            q = q.filter(FictionalLme.cid10 == plan["cid"])
        return q

    def _retrieve(self, plan: dict[str, Any], db: Session, question: str = "") -> dict[str, Any]:
        intent = plan["intent"]
        if intent == "fornecedores":
            return self._suppliers(plan)
        if intent == "medicamentos":
            return self._medicines(plan)
        if intent == "lmes-pendentes":
            return self._pending_lmes(plan, db)
        if intent == "lmes-por-cid":
            return self._by_cid(plan, db)
        if intent == "pacientes":
            return self._patients(plan, db)
        if intent == "contagem":
            return self._counts(plan, db, question)
        return self._overview(db)

    def _suppliers(self, plan: dict[str, Any]) -> dict[str, Any]:
        rows = FORNECEDORES
        city = plan.get("cidade")
        if city:
            rows = [f for f in FORNECEDORES if city.lower() in f[2].lower()]
        if plan.get("termo"):
            termo = str(plan["termo"]).lower()
            rows = [f for f in rows if termo in " ".join(f).lower()]
        cols = ["CNPJ", "Razão Social", "Cidade", "UF", "Contato", "Telefone", "Endereço"]
        data = [[f[0], f[1], f[2], uf_do_municipio(f[2]), f[3], f[4], f[5]] for f in rows]
        where = f" em {_cidade_label(city)}" if city else ""
        return {
            "answer": f"Fornecedores encontrados{where}: {len(data)} registro(s).",
            "columns": cols,
            "rows": data,
            "intent": "fornecedores",
            "model": "consulta-direta",
            "facts": {
                "total": len(data),
                "cidade": city,
                "amostra": data[:6],
            },
        }

    def _medicines(self, plan: dict[str, Any]) -> dict[str, Any]:
        termo = (plan.get("termo") or "").lower()
        rows = [m for m in MEDICAMENTOS if not termo or termo in " ".join(m).lower()]
        cols = ["Código", "Nome", "Princípio Ativo", "Apresentação"]
        data = [[m[0], m[1], m[2], m[3]] for m in rows]
        return {
            "answer": f"Medicamentos encontrados: {len(data)}.",
            "columns": cols,
            "rows": data,
            "intent": "medicamentos",
            "model": "consulta-direta",
            "facts": {"total": len(data), "filtro": termo or None, "amostra": data[:6]},
        }

    def _patients(self, plan: dict[str, Any], db: Session) -> dict[str, Any]:
        q = self._user_query(db, plan)
        total = q.count()
        limite = 12000 if plan.get("todos") else 100
        rows = q.order_by(FictionalUser.id).limit(limite).all()
        cols = ["ID", "Paciente", "CNS", "Unidade", "Município", "UF"]
        data = [[u.id, u.nome, u.cns_ficticio, u.unidade, u.municipio, u.uf] for u in rows]
        por_unidade = dict(
            q.with_entities(FictionalUser.unidade, func.count(FictionalUser.id))
            .group_by(FictionalUser.unidade).all()
        )
        por_municipio: dict[str, int] = {}
        for unidade, quantidade in por_unidade.items():
            municipio = self.UNIDADE_CIDADE.get(str(unidade), "Não informado")
            por_municipio[municipio] = por_municipio.get(municipio, 0) + int(quantidade)
        cidade = plan.get("cidade")
        cidade_label = _cidade_label(cidade)
        where = f" em {cidade_label}" if cidade_label else ""
        return {
            "answer": f"Pacientes encontrados{where}: {total}. Exibindo {len(data)}.",
            "columns": cols,
            "rows": data,
            "intent": "pacientes",
            "model": "consulta-direta",
            # Sem nomes/CNS: só agregados para o modelo redigir.
            "facts": {
                "total": total,
                "cidade": cidade_label or None,
                "por_unidade": por_unidade,
                "por_municipio": por_municipio,
                "exibindo": len(data),
            },
        }

    def _pending_lmes(self, plan: dict[str, Any], db: Session) -> dict[str, Any]:
        q = self._lme_query(db, plan, status="pendente")
        total = q.count()
        rows = q.with_entities(FictionalLme, FictionalUser).order_by(
            FictionalLme.id).limit(100).all()
        cols = ["LME", "Medicamento", "Paciente", "Unidade", "Município", "UF", "CID", "Emissão"]
        data = [
            [f"LME-{l.id:06d}", l.medicamento, u.nome, u.unidade, u.municipio, u.uf,
             l.cid10,
             l.created_at.strftime("%d/%m/%Y") if l.created_at else ""]
            for l, u in rows
        ]
        por_medicamento = dict(
            q.with_entities(FictionalLme.medicamento, func.count(FictionalLme.id))
            .group_by(FictionalLme.medicamento).order_by(
                func.count(FictionalLme.id).desc()).limit(6).all()
        )
        return {
            "answer": f"Existem {total} LMEs aguardando autorização"
                      f"{' em ' + _cidade_label(plan.get('cidade')) if plan.get('cidade') else ''}. "
                      f"Relação abaixo (até 100):",
            "columns": cols,
            "rows": data,
            "intent": "lmes-pendentes",
            "model": "consulta-direta",
            "facts": {
                "total": total,
                "cidade": plan.get("cidade"),
                "por_medicamento": por_medicamento,
                "exibindo": len(data),
            },
        }

    def _by_cid(self, plan: dict[str, Any], db: Session) -> dict[str, Any]:
        q = self._lme_query(db, plan)
        total = q.count()
        rows = q.with_entities(FictionalLme, FictionalUser).order_by(
            FictionalLme.id).limit(100).all()
        cols = ["LME", "Medicamento", "Paciente", "Unidade", "Município", "UF", "CID", "Status"]
        data = [[f"LME-{l.id:06d}", l.medicamento, u.nome, u.unidade, u.municipio,
                 u.uf, l.cid10, l.status] for l, u in rows]
        cid = plan.get("cid") or "não informado"
        return {
            "answer": f"LMEs por CID {cid}: {total} registro(s). Exibindo {len(data)}.",
            "columns": cols,
            "rows": data,
            "intent": "lmes-por-cid",
            "model": "consulta-direta",
            "facts": {
                "total": total,
                "cid": cid,
                "cidade": plan.get("cidade"),
                "por_status": dict(
                    q.with_entities(FictionalLme.status, func.count(FictionalLme.id))
                    .group_by(FictionalLme.status).all()
                ),
            },
        }

    def _counts(self, plan: dict[str, Any], db: Session, question: str = "") -> dict[str, Any]:
        ql = question.lower()
        entidade = plan.get("entidade")
        if not entidade:
            if "paciente" in ql:
                entidade = "pacientes"
            elif "medicamento" in ql or "remédio" in ql or "remedio" in ql:
                entidade = "medicamentos"
            elif "fornecedor" in ql or "distribuidora" in ql:
                entidade = "fornecedores"
            elif "lme" in ql:
                entidade = "lmes"
            else:
                entidade = "pacientes"

        cidade = plan.get("cidade")
        cidade_label = _cidade_label(cidade)
        where = f" em {cidade_label}" if cidade_label else ""
        if entidade == "medicamentos":
            total, label = len(MEDICAMENTOS), "medicamentos cadastrados"
        elif entidade == "fornecedores":
            rows = FORNECEDORES
            if cidade:
                rows = [f for f in FORNECEDORES if cidade.lower() in f[2].lower()]
            total, label = len(rows), f"fornecedores cadastrados{where}"
        elif entidade == "lmes":
            q = self._lme_query(db, plan)
            total, label = q.count(), f"LMEs no sistema{where}"
        else:
            q = self._user_query(db, plan)
            total, label = q.count(), f"pacientes cadastrados{where}"
        return {
            "answer": f"Existem {total} {label}.",
            "columns": ["Indicador", "Valor"],
            "rows": [[label[0].upper() + label[1:], total]],
            "intent": "contagem",
            "model": "consulta-direta",
            "facts": {"entidade": entidade, "total": total,
                      "rotulo": label, "cidade": cidade_label or None},
        }

    def _overview(self, db: Session) -> dict[str, Any]:
        total = db.query(func.count(FictionalLme.id)).scalar() or 0
        users = db.query(func.count(FictionalUser.id)).scalar() or 0
        by_status = dict(db.query(FictionalLme.status, func.count(FictionalLme.id))
                         .group_by(FictionalLme.status).all())
        cols = ["Indicador", "Valor"]
        data = [["LMEs no sistema", total], ["Pacientes", users],
                *[[k, v] for k, v in by_status.items()]]
        return {
            "answer": "Visão geral da operação:",
            "columns": cols,
            "rows": data,
            "intent": "visao-geral",
            "model": "consulta-direta",
            "facts": {"total_lmes": total, "total_pacientes": users,
                      "por_status": by_status},
        }

    # ------------------------------------------------------------------ #
    # 3) Gemini redige a resposta final (sem dados pessoais no prompt)
    # ------------------------------------------------------------------ #
    def _draft(self, question: str, plan: dict[str, Any],
               result: dict[str, Any], planner: str) -> dict[str, Any]:
        result["model"] = planner
        if not self.settings.gemini_api_key:
            return result
        prompt = f"""Você é o copiloto farmacêutico do AF Copilot (SESAB).
Redija a RESPOSTA FINAL em português brasileiro, em 1 a 3 frases objetivas,
usando SOMENTE os números e filtros do resumo abaixo. Não invente dados.
Não cite nomes de pacientes (o resumo já vem sem dados pessoais).
Se o total for zero, diga que não há registros para o filtro.

PERGUNTA: {json.dumps(question, ensure_ascii=False)}
PLANO: {json.dumps(plan, ensure_ascii=False)}
RESUMO AGREGADO: {json.dumps(result.get("facts", {}), ensure_ascii=False, default=str)}
RESPOSTA BASE: {json.dumps(result.get("answer", ""), ensure_ascii=False)}

Responda apenas com o texto final, sem JSON e sem markdown."""
        models = [self.settings.gemini_model, *self.settings.gemini_fallback_models]
        for name in dict.fromkeys(models):
            try:
                text = self._invoke(name, prompt).strip().strip('"')
                if text:
                    result["answer"] = text[:600]
                    result["model"] = name
                    return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("Modelo %s falhou ao redigir a resposta: %s", name, exc)
        # Honestidade: o plano pode ter vindo do Gemini, mas a redação foi local.
        result["model"] = (
            "roteador-local" if planner == "roteador-local" else f"{planner} (plano; redação local)"
        )
        return result

    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse(raw: str) -> dict[str, Any]:
        match = _JSON.search(raw)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
