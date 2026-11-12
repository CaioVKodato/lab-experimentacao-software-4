"""Geração de dados simulados (pares sem/com cache) a partir de data/params.json."""

from .gerador import DEFAULT_SEED, gerar_pares, load_sim_params
from .motor import GERADORES, REPETICOES, Cenario, simular_cenario

__all__ = [
    "DEFAULT_SEED",
    "GERADORES",
    "REPETICOES",
    "Cenario",
    "gerar_pares",
    "load_sim_params",
    "simular_cenario",
]
