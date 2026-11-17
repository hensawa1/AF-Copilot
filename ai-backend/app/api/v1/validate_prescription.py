"""POST /api/v1/validate-prescription — validador multimodal de receita/LME."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from ...core.auth_deps import require_perfil
from ...core.database import get_session
from ...core.security import verify_internal_token
from ...models.operational import AuditLog
from ...schemas.requests import ContextPayload
from ...schemas.responses import ValidationResponse
from ...services.file_validation import read_validated_upload

router = APIRouter()


@router.post("/validate-prescription", response_model=ValidationResponse)
async def validate_prescription(
    request: Request,
    file: UploadFile = File(...),
    context: str = Form("{}"),
    _auth: None = Depends(verify_internal_token),
    user=Depends(require_perfil("Administrador", "Farmacêutico", "Auditor")),
    db: Session = Depends(get_session),
) -> ValidationResponse:
    settings = request.app.state.settings
    content, mime = await read_validated_upload(file, settings)

    # Cliente pode enviar '{}' (sem contexto capturado) quando o farmacêutico
    # sobe a receita antes de selecionar algo no portal.
    if context.strip() in {"", "null", "{}"}:
        context = '{"capturedAt": "1970-01-01T00:00:00Z"}'

    try:
        parsed = ContextPayload.model_validate_json(context)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Contexto inválido: {exc}",
        ) from exc

    result = request.app.state.vision.validate(
        content=content,
        mime=mime,
        context_summary=parsed.summary,
        context_drugs=parsed.drugs,
        context_cid=parsed.cid10,
    )

    db.add(AuditLog(
        actor=user.username,
        acao="validacao_receita_ia",
        entidade="receita",
        entidade_id="",
        detalhes=(
            f"perfil={user.perfil} | status={result.status} | "
            f"farmacos={','.join(parsed.drugs)} | cid={','.join(parsed.cid10)}"
        ),
    ))
    db.commit()
    request.app.state.audit.log_event(
        "validate_prescription",
        {
            "usuario": user.username,
            "perfil": user.perfil,
            "status": result.status,
            "drugs": parsed.drugs,
            "cid10": parsed.cid10,
            "file_type": mime,
        },
    )
    return result
