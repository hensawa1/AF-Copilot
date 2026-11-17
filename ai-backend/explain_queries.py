"""Identifica consultas lentas e grava os planos de execução (EXPLAIN QUERY PLAN)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.core.database import engine

OUT = Path(__file__).resolve().parents[1] / "docs" / "planos-execucao.txt"

QUERIES = [
    ("Lenta 1 — filtro por medicamento sem índice (LIKE '%...')",
     "EXPLAIN QUERY PLAN SELECT * FROM fictional_lmes WHERE medicamento LIKE '%Metformina%' LIMIT 100"),
    ("Otimizada 1 — filtro por status com índice",
     "EXPLAIN QUERY PLAN SELECT * FROM fictional_lmes WHERE status = 'faturada' LIMIT 100"),
    ("Lenta 2 — varredura de usuários por e-mail sem índice se removido",
     "EXPLAIN QUERY PLAN SELECT * FROM fictional_users WHERE email LIKE '%arlindo%' LIMIT 10"),
    ("Lenta 3 — busca textual por nome de paciente (usada pela IA)",
     "EXPLAIN QUERY PLAN SELECT * FROM fictional_users WHERE nome LIKE '%Arlindo%' LIMIT 100"),
    ("Otimizada 2 — busca por e-mail com índice único",
     "EXPLAIN QUERY PLAN SELECT * FROM fictional_users WHERE email = 'ficticio.000001@email.com'"),
    ("Otimizada 3 — contagem de pacientes por unidade (Município/UF)",
     "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM fictional_users WHERE unidade = 'UBS Fictícia Gandu'"),
    ("Otimizada 4 — contagem de LMEs por CID",
     "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM fictional_lmes WHERE cid10 = 'E11'"),
    ("Otimizada 5 — LMEs pendentes por unidade (status + paciente)",
     "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM fictional_lmes WHERE status = 'pendente' "
     "AND user_id IN (SELECT id FROM fictional_users WHERE unidade = 'UBS Fictícia Gandu')"),
    ("Agregação — contagem por status",
     "EXPLAIN QUERY PLAN SELECT status, COUNT(*) FROM fictional_lmes GROUP BY status"),
]


def main() -> None:
    lines = ["PLANOS DE EXECUÇÃO — SQLITE (AF Copilot)", "=" * 70, ""]
    with engine.connect() as conn:
        for title, sql in QUERIES:
            rows = conn.execute(text(sql)).all()
            lines.append(title)
            lines.append("  SQL: " + sql.replace("EXPLAIN QUERY PLAN ", ""))
            for r in rows:
                lines.append("  -> " + " | ".join(str(x) for x in r))
            lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"salvo em {OUT}")


if __name__ == "__main__":
    main()
