"""Geração de dados simulados (pares sem/com cache) a partir de data/params.json."""

from .gerador import DEFAULT_SEED, gerar_pares, load_sim_params

__all__ = ["DEFAULT_SEED", "gerar_pares", "load_sim_params"]
