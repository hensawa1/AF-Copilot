"""Login local do aplicativo (usuário do trabalho acadêmico)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.database import get_session
from ...models.app_user import AppUser
from ...models.operational import AppSession, AuditLog

router = APIRouter()

# Proteção simples contra força bruta (memória do processo, sem dependências).
_JANELA_SEG = 300.0
_MAX_FALHAS_CONTA = 8
_MAX_FALHAS_IP = 30
_TENTATIVAS: dict[str, Deque[float]] = defaultdict(deque)


def _podar(fila: Deque[float], agora: float) -> None:
    while fila and agora - fila[0] > _JANELA_SEG:
        fila.popleft()


def _excedeu(chave: str, limite: int, agora: float) -> bool:
    fila = _TENTATIVAS[chave]
    _podar(fila, agora)
    return len(fila) >= limite


def _registrar_falha(*chaves: str, agora: float) -> None:
    for chave in chaves:
        _TENTATIVAS[chave].append(agora)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    username: str
    nome: str
    perfil: str
    unidade: str
    session_token: str


def hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000).hex()


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_session),
) -> LoginResponse:
    agora = time.monotonic()
    ip = request.client.host if request.client else "desconhecido"
    conta = f"conta:{ip}:{payload.username.strip().lower()}"
    chave_ip = f"ip:{ip}"

    if _excedeu(conta, _MAX_FALHAS_CONTA, agora) or _excedeu(chave_ip, _MAX_FALHAS_IP, agora):
        db.add(AuditLog(
            actor=payload.username, acao="login_bloqueado", entidade="sessao",
            entidade_id=payload.username, detalhes=f"ip={ip} (rate limit)",
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Aguarde 5 minutos.",
            headers={"Retry-After": "300"},
        )

    user = db.query(AppUser).filter(AppUser.username == payload.username).first()
    if user is None:
        _registrar_falha(conta, chave_ip, agora=agora)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")

    candidate = hash_password(payload.password, bytes.fromhex(user.salt))
    if not hmac.compare_digest(candidate, user.password_hash):
        _registrar_falha(conta, chave_ip, agora=agora)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")

    # Login válido zera o contador daquela conta (o do IP expira pela janela).
    _TENTATIVAS.pop(conta, None)
    token = secrets.token_urlsafe(32)
    db.add(AppSession(token=token, username=user.username))
    db.add(AuditLog(
        actor=user.username, acao="login", entidade="sessao",
        entidade_id=user.username, detalhes=f"perfil={user.perfil}",
    ))
    db.commit()
    return LoginResponse(
        username=user.username,
        nome=user.nome,
        perfil=user.perfil,
        unidade=user.unidade,
        session_token=token,
    )
