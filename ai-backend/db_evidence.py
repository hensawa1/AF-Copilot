"""Coleta evidências de integridade, volume e índices do SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = Path(__file__).resolve().parent / "runtime" / "af_copilot.db"
OUT = ROOT / "docs" / "evidencias" / "indices.txt"


def main() -> None:
    con = sqlite3.connect(DB)
    linhas: list[str] = ["INTEGRIDADE, VOLUME E ÍNDICES — SQLITE", "=" * 70, ""]

    integridade = con.execute("PRAGMA integrity_check").fetchone()[0]
    linhas.append(f"PRAGMA integrity_check: {integridade}")
    linhas.append("")

    linhas.append("VOLUME")
    for tabela in ("fictional_users", "fictional_lmes", "catalog_medications", "audit_logs"):
        total = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        linhas.append(f"  {tabela}: {total:,}".replace(",", "."))
    linhas.append("")

    linhas.append("ÍNDICES")
    for tabela in ("fictional_users", "fictional_lmes"):
        for row in con.execute(f"PRAGMA index_list('{tabela}')"):
            nome = row[1]
            colunas = [r[2] for r in con.execute(f"PRAGMA index_info('{nome}')")]
            linhas.append(f"  {tabela}.{nome}: {', '.join(colunas)}")
    linhas.append("")

    linhas.append("PLANOS OTIMIZADOS")
    consultas = [
        ("Pacientes por unidade (cidade)", 
         "SELECT COUNT(*) FROM fictional_users WHERE unidade = 'UBS Fictícia Gandu'"),
        ("LMEs por CID",
         "SELECT COUNT(*) FROM fictional_lmes WHERE cid10 = 'E11'"),
        ("LMEs pendentes por paciente de uma unidade",
         "SELECT COUNT(*) FROM fictional_lmes WHERE status = 'pendente' "
         "AND user_id IN (SELECT id FROM fictional_users WHERE unidade = 'UBS Fictícia Gandu')"),
    ]
    for titulo, sql in consultas:
        linhas.append(f"  {titulo}:")
        for row in con.execute("EXPLAIN QUERY PLAN " + sql):
            linhas.append("    -> " + " | ".join(str(x) for x in row))
    con.close()

    OUT.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"\nsalvo em {OUT}")


if __name__ == "__main__":
    main()
