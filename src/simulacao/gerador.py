from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_SEED = 42
CONDICOES = ("sem_cache", "com_cache")


def load_sim_params(path: Path) -> dict[str, Any]:
    """Lê o bloco `simulacao` de data/params.json e valida o básico."""
    if not path.exists():
        raise FileNotFoundError(f"params não encontrado: {path}")

    params = json.loads(path.read_text(encoding="utf-8"))
    sim = params.get("simulacao")
    if sim is None:
        raise ValueError("params.json sem o bloco 'simulacao'")
    if sim.get("distribuicao") != "lognormal":
        raise ValueError(f"distribuição não suportada: {sim.get('distribuicao')}")
    for cond in CONDICOES:
        if cond not in sim or not {"mu", "sigma"} <= set(sim[cond]):
            raise ValueError(f"params de '{cond}' sem mu/sigma")
    return sim


def gerar_pares(
    sim: dict[str, Any],
    n: int | None = None,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """
    Gera n pares (sem_cache, com_cache) de tempos de build.

    Cada condição segue uma lognormal com mu/sigma em log(tempo_s).
    Saída no mesmo formato de data/builds.csv (run, condicao, tempo_s),
    então serve tanto pro G1 quanto pros testes pareados.
    """
    n = int(sim["n_por_grupo"]) if n is None else int(n)
    if n < 1:
        raise ValueError("n precisa ser >= 1")
    rng = np.random.default_rng(DEFAULT_SEED) if rng is None else rng

    sem = rng.lognormal(sim["sem_cache"]["mu"], sim["sem_cache"]["sigma"], size=n)
    com = rng.lognormal(sim["com_cache"]["mu"], sim["com_cache"]["sigma"], size=n)

    runs = np.arange(1, n + 1)
    return pd.DataFrame(
        {
            "run": np.repeat(runs, 2),
            "condicao": np.tile(CONDICOES, n),
            "tempo_s": np.column_stack([sem, com]).ravel(),
        }
    )
