"""Mede latência real do pipeline Gemini (plano + redação) e do cache TTL."""

from __future__ import annotations

import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
INTERNAL = (Path(__file__).resolve().parent / "runtime" / "auth_token").read_text(encoding="utf-8").strip()
OUT = Path(__file__).resolve().parents[1] / "docs" / "evidencias" / "latencia_ia.txt"

PERGUNTAS = [
    "Quais LMEs estão pendentes em Feira de Santana?",
    "Quais LMEs estão pendentes em Feira de Santana?",
    "Quantos pacientes existem em Vitória da Conquista?",
    "Quantos pacientes existem em Vitória da Conquista?",
]


def main() -> None:
    linhas = ["LATÊNCIA DO PIPELINE GEMINI — AF COPILOT", "=" * 70, ""]
    with httpx.Client(base_url=BASE, timeout=120) as c:
        token = c.post(
            "/auth/login",
            json={"username": "henriquecarvalho", "password": "3246Hz!@#Hz"},
        ).json()["session_token"]
        headers = {"X-Internal-Auth-Token": INTERNAL, "X-Session-Token": token}
        for pergunta in PERGUNTAS:
            inicio = time.perf_counter()
            resposta = c.post("/admin/ask", json={"pergunta": pergunta}, headers=headers)
            ms = (time.perf_counter() - inicio) * 1000
            dados = resposta.json()
            linha = (
                f"{ms:8.1f} ms | modelo={dados.get('model')} | intencao={dados.get('intent')} "
                f"| linhas={len(dados.get('rows') or [])} | {dados.get('answer', '')[:140]}"
            )
            print(linha)
            linhas.append(linha)
    OUT.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nsalvo em {OUT}")


if __name__ == "__main__":
    main()
