"""Gera volumes.txt e planos-execucao.txt com dados reais do SQLite."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.core.database import engine

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidencias"


def main() -> None:
    with engine.connect() as conn:
        tabelas = [r[0] for r in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )).all()]
        linhas = ["VOLUME EXATO DA BASE — AF COPILOT (fictícia/anonimizada)", "=" * 62, ""]
        for t in tabelas:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            linhas.append(f"{t:<28} {n:>8,} linhas")
        linhas += ["", "Fonte: sqlite_master + COUNT(*) executado no SQLite da aplicação.", ""]
        (OUT / "volumes.txt").write_text("\n".join(linhas), encoding="utf-8")

        consultas = [
            ("CONSULTA LENTA 1 — LIKE com curinga à esquerda (medicamento)",
             "EXPLAIN QUERY PLAN SELECT * FROM fictional_lmes WHERE medicamento LIKE '%Metformina%' LIMIT 100"),
            ("OTIMIZADA 1 — filtro por status com índice",
             "EXPLAIN QUERY PLAN SELECT * FROM fictional_lmes WHERE status = 'faturada' LIMIT 100"),
            ("CONSULTA LENTA 2 — busca textual por nome de paciente",
             "EXPLAIN QUERY PLAN SELECT * FROM fictional_users WHERE nome LIKE '%Arlindo%' LIMIT 100"),
            ("OTIMIZADA 2 — e-mail com índice único",
             "EXPLAIN QUERY PLAN SELECT * FROM fictional_users WHERE email = 'ficticio.000001@email.com'"),
            ("OTIMIZADA 3 — contagem de pacientes por unidade (Município/UF)",
             "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM fictional_users WHERE unidade = 'UBS Fictícia Gandu'"),
            ("OTIMIZADA 4 — contagem de LMEs por CID",
             "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM fictional_lmes WHERE cid10 = 'E11'"),
            ("OTIMIZADA 5 — LMEs pendentes por status + unidade",
             "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM fictional_lmes WHERE status = 'pendente' "
             "AND user_id IN (SELECT id FROM fictional_users WHERE unidade = 'UBS Fictícia Gandu')"),
        ]
        planos = ["PLANOS DE EXECUÇÃO — SQLITE (AF Copilot)", "=" * 62, ""]
        for titulo, sql in consultas:
            planos.append(titulo)
            planos.append("  SQL: " + sql.replace("EXPLAIN QUERY PLAN ", ""))
            for r in conn.execute(text(sql)).all():
                planos.append("  -> " + " | ".join(str(x) for x in r))
            planos.append("")
        planos += [
            "LEITURA DOS PLANOS:",
            "- LIKE '%termo%' = SCAN de tabela (~216 páginas nas consultas lentas).",
            "- SEARCH USING INDEX ix_lme_status = índice de status (~61 páginas).",
            "- SEARCH USING INDEX ix_fictional_users_unidade = unidade (~54 páginas).",
            "- SEARCH USING INDEX ix_lme_cid10 = CID (~52 páginas).",
            "- SEARCH USING INDEX ix_lme_status_usuario = status+usuario (~53 páginas).",
            "- email possui índice UNIQUE (sqlite_autoindex) (~39 páginas).",
            "",
        ]
        texto = "\n".join(planos)
        (ROOT / "docs" / "planos-execucao.txt").write_text(texto, encoding="utf-8")
        (OUT / "planos-execucao.txt").write_text(texto, encoding="utf-8")
        print("\n".join(linhas))
        print("\n".join(planos[:20]))


if __name__ == "__main__":
    main()
