"""Cria/atualiza os papéis de acesso para a entrega de Segurança.

Senhas lidas de variáveis de ambiente (nunca gravadas no repositório):
  AF_ADMIN_USER / AF_ADMIN_PASSWORD
  AF_FARM_USER  / AF_FARM_PASSWORD
  AF_AUDIT_USER / AF_AUDIT_PASSWORD
"""

from __future__ import annotations

import os
import secrets

from app.api.v1.auth import hash_password
from app.core.database import SessionLocal, init_db
from app.models.app_user import AppUser

ROLES = [
    ("ADMIN", "Administrador", "AF_ADMIN_USER", "AF_ADMIN_PASSWORD"),
    ("FARM", "Farmacêutico", "AF_FARM_USER", "AF_FARM_PASSWORD"),
    ("AUDIT", "Auditor", "AF_AUDIT_USER", "AF_AUDIT_PASSWORD"),
    ("ASSIST", "Assistente", "AF_ASSIST_USER", "AF_ASSIST_PASSWORD"),
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        for key, perfil, user_env, pass_env in ROLES:
            username = os.environ.get(user_env, "").strip()
            password = os.environ.get(pass_env, "")
            if not username or not password:
                print(f"pulando {perfil}: {user_env}/{pass_env} nao definidos")
                continue
            salt = secrets.token_bytes(16)
            user = db.query(AppUser).filter(AppUser.username == username).first()
            if user is None:
                user = AppUser(username=username)
                db.add(user)
            user.salt = salt.hex()
            user.password_hash = hash_password(password, salt)
            user.perfil = perfil
            user.nome = f"Usuario {perfil}"
            user.unidade = "5ª DIRETORIA REGIONAL DE SAÚDE - GANDU"
            print(f"perfil {perfil}: {username}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
