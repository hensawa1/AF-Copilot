"""Insights de IA para o administrador."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ...core.auth_deps import require_perfil
from ...core.database import get_session
from ...core.logging import get_logger
from ...core.security import verify_internal_token
from ...models.app_user import AppUser
from ...models.operational import AuditLog
from ...schemas.responses import AdminInsightsResponse
from ...services.admin_ask import AdminAskService
from ...services.prompt_guard import PromptGuard
from sqlalchemy.orm import Session

router = APIRouter()
logger = get_logger(__name__)


class InsightsRequest(BaseModel):
    foco: str = Field(default="geral", max_length=80)


class AskRequest(BaseModel):
    pergunta: str = Field(min_length=3, max_length=300)


class AskResponse(BaseModel):
    answer: str
    columns: list[str]
    rows: list[list[object]]
    intent: str
    model: str
    suggestions: list[str]
    security_notice: str = ""


@router.post("/admin/audit")
async def admin_audit(
    request: Request,
    db: Session = Depends(get_session),
    _auth: None = Depends(verify_internal_token),
) -> dict[str, object]:
    achados = request.app.state.insights.audit(db)
    return {"total": len(achados), "achados": achados}


@router.post("/admin/ask", response_model=AskResponse)
async def admin_ask(
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_session),
    user: AppUser = Depends(require_perfil("Administrador", "Farmacêutico", "Auditor", "Assistente")),
    _auth: None = Depends(verify_internal_token),
) -> AskResponse:
    check = PromptGuard.analyze(payload.pergunta)
    if not check.safe:
        logger.warning("Prompt injection detectado em /admin/ask: %s", check.reasons[:2])
        result = AdminAskService(request.app.state.settings).answer("visão geral", db)
        result["security_notice"] = "Entrada bloqueada: foi detectada uma tentativa de manipulação de instruções."
        intent = "bloqueio-seguranca"
    else:
        result = AdminAskService(request.app.state.settings).answer(check.sanitized, db)
        intent = result["intent"]

        # INTEGRAÇÃO: a IA respeita as permissões do perfil — nem por meio dela
        # um perfil sem permissão obtém dados nominalmente de pacientes.
        # Política de menor privilégio:
        # - Administrador/Auditor: acesso completo.
        # - Farmacêutico: pode consultar pacientes e LMEs (necessário ao cuidado).
        # - Assistente: só dados agregados/genéricos; qualquer intenção que
        #   retorne pacientes ou LMEs nominalmente é negada, mesmo via IA.
        perfis_restritos = {"Assistente"}
        intencoes_com_paciente = {"pacientes", "lmes-pendentes", "lmes-por-cid"}
        if intent in intencoes_com_paciente and user.perfil in perfis_restritos:
            result["rows"] = []
            result["answer"] = "Acesso negado: seu perfil não pode consultar dados de pacientes."
            result["security_notice"] = f"RBAC aplicado à IA para o perfil {user.perfil}."

    # Auditoria: o que a IA consultou, quem pediu e quando.
    result.setdefault("suggestions", [
        "Qual o fornecedor de Salvador?",
        "Quais pacientes são de Salvador?",
        "Quantos medicamentos estão cadastrados?",
    ])
    result.setdefault("security_notice", "")
    db.add(AuditLog(
        actor=user.username,
        acao="consulta_ia",
        entidade=str(intent),
        entidade_id="",
        detalhes=f"pergunta={check.sanitized[:200]} | perfil={user.perfil} | linhas={len(result['rows'])}",
    ))
    db.commit()
    return AskResponse(**result)


@router.post("/admin/insights", response_model=AdminInsightsResponse)
async def admin_insights(
    payload: InsightsRequest,
    request: Request,
    db: Session = Depends(get_session),
    user: AppUser = Depends(require_perfil("Administrador", "Farmacêutico", "Auditor", "Assistente")),
    _auth: None = Depends(verify_internal_token),
) -> AdminInsightsResponse:
    check = PromptGuard.analyze(payload.foco, max_length=80)
    foco = "geral" if not check.safe else check.sanitized
    if not check.safe:
        logger.warning("Prompt injection detectado em /admin/insights: %s", check.reasons[:2])
    result = request.app.state.insights.generate(db, foco)
    if not check.safe and not result.resumo.startswith("Entrada bloqueada"):
        result.resumo = "Entrada bloqueada por segurança. " + result.resumo

    db.add(AuditLog(
        actor=user.username,
        acao="insights_ia",
        entidade="insights",
        entidade_id=foco,
        detalhes=f"perfil={user.perfil} | modelo={result.model}",
    ))
    db.commit()
    return result
