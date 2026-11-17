"""Territorialização fictícia — unidade de saúde -> Município/UF.

Fonte única para exibição em TODAS as telas (pacientes, farmácias, LMEs,
fornecedores, relatórios). Sem dependência de outros módulos para evitar
import circular com os modelos SQLAlchemy.
"""

from __future__ import annotations

# Unidade -> (Município, UF)
UNIDADE_TERRITORIO: dict[str, tuple[str, str]] = {
    "UBS Centro": ("Gandu", "BA"),
    "UBS Jardim Primavera": ("Gandu", "BA"),
    "UBS Vila Nova": ("Gandu", "BA"),
    "UPA Leste": ("Gandu", "BA"),
    "Hospital Municipal Dr. João Silva": ("Salvador", "BA"),
    "UBS Praia Grande": ("Salvador", "BA"),
    "UBS Nova Esperança": ("Feira de Santana", "BA"),
    "Hospital Regional Sul": ("Vitória da Conquista", "BA"),
}

# Município -> UF (fornecedores e demais cadastros municipais).
UF_POR_MUNICIPIO: dict[str, str] = {
    "Gandu": "BA",
    "Salvador": "BA",
    "Feira de Santana": "BA",
    "Vitória da Conquista": "BA",
    "São Paulo": "SP",
    "Recife": "PE",
    "Porto Alegre": "RS",
    "Belo Horizonte": "MG",
}


def municipio_da_unidade(unidade: str) -> str:
    return UNIDADE_TERRITORIO.get(unidade, ("", ""))[0]


def uf_da_unidade(unidade: str) -> str:
    return UNIDADE_TERRITORIO.get(unidade, ("", ""))[1]


def uf_do_municipio(municipio: str) -> str:
    return UF_POR_MUNICIPIO.get(municipio, "")
