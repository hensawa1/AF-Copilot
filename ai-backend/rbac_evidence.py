"""Gera evidências de RBAC: acesso permitido, negado e IA respeitando permissões."""

from __future__ import annotations

from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
INTERNAL = (Path(__file__).resolve().parent / "runtime" / "auth_token").read_text(encoding="utf-8").strip()
OUT = Path(__file__).resolve().parents[1] / "docs" / "evidencias" / "rbac.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

USERS = [
    ("Administrador", "admin.sesab", "Adm@2026!Senha"),
    ("Farmacêutico", "henriquecarvalho", "3246Hz!@#Hz"),
    ("Auditor", "auditor.sesab", "Aud@2026!Senha"),
    ("Assistente", "assistente.farma", "Assist@2026!Senha"),
]


def main() -> None:
    lines = ["EVIDÊNCIAS DE RBAC — AF COPILOT", "=" * 60, ""]
    with httpx.Client(base_url=BASE, timeout=60) as c:
        for perfil, user, password in USERS:
            r = c.post("/auth/login", json={"username": user, "password": password})
            token = r.json().get("session_token", "")
            H = {"X-Session-Token": token, "X-Internal-Auth-Token": INTERNAL,
                 "Content-Type": "application/json"}
            lines.append(f"PERFIL: {perfil} ({user})")
            lines.append(f"  login -> {r.status_code}")

            r = c.get("/fictional/audit", headers=H)
            lines.append(f"  GET /fictional/audit ............ {r.status_code} "
                         f"{'PERMITIDO' if r.status_code == 200 else 'NEGADO'}")

            r = c.get("/fictional/audit/export?formato=csv", headers=H)
            lines.append(f"  GET /fictional/audit/export ..... {r.status_code} "
                         f"{'PERMITIDO' if r.status_code == 200 else 'NEGADO'}")

            r = c.post("/fictional/medicamentos", headers=H, json={
                "nome": "Medicamento Teste RBAC", "principio": "Principio", "apresentacao": "Comprimido 10 mg",
            })
            lines.append(f"  POST /fictional/medicamentos .... {r.status_code} "
                         f"{'PERMITIDO' if r.status_code == 200 else 'NEGADO'}")

            r = c.post("/admin/ask", headers=H, json={"pergunta": "Arlindo"})
            data = r.json()
            lines.append(f"  IA /admin/ask 'Arlindo' ........ {r.status_code} "
                         f"| linhas={len(data.get('rows', []))} | {data.get('security_notice') or data.get('answer', '')[:70]}")
            lines.append("")

        # Auditoria da IA: quem perguntou o quê e quando
        r = c.post("/auth/login", json={"username": "admin.sesab", "password": "Adm@2026!Senha"})
        H = {"X-Session-Token": r.json()["session_token"], "X-Internal-Auth-Token": INTERNAL}
        resp = c.get("/fictional/audit", headers=H)
        logs = resp.json()
        lines.append(f"  GET /fictional/audit (admin) -> {resp.status_code}")
        if not isinstance(logs, list):
            lines.append(f"  resposta inesperada: {str(logs)[:200]}")
            logs = []
        ia_logs = [l for l in logs if isinstance(l, dict) and l.get("acao") in ("consulta_ia", "insights_ia")]
        lines.append("AUDITORIA DA IA (o que consultou, quem pediu, quando):")
        for l in ia_logs[:8]:
            lines.append(f"  {l['created_at'][:19]} | {l['actor']} | {l['acao']} | {l['entidade']} | {l['detalhes'][:90]}")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"salvo em {OUT}")


if __name__ == "__main__":
    main()
