from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

CONDICOES = {"sem_cache": "Sem cache", "com_cache": "Com cache"}
# cores fixas por origem do dado; os testes ganham as próprias no G2–G4
COR_REAL = "#4C72B0"
COR_SIMULADO = "#DD8452"
COR_LOGNORMAL = "#333333"


def fig_g1(
    reais: pd.DataFrame,
    simulados: pd.DataFrame,
    sim_params: dict[str, Any] | None = None,
    bins: int = 10,
) -> plt.Figure:
    """
    G1: histograma dos dados reais ao lado dos simulados, um painel por condição.

    Real e simulado dividem os mesmos bins em cada painel, para comparar a forma.
    Com sim_params, desenha a densidade lognormal usada na simulação.
    """
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)

    for ax, (cond, rotulo) in zip(axes, CONDICOES.items()):
        real = reais.loc[reais["condicao"] == cond, "tempo_s"].to_numpy(dtype=float)
        sim = simulados.loc[simulados["condicao"] == cond, "tempo_s"].to_numpy(dtype=float)

        lo = min(real.min(), sim.min())
        hi = max(real.max(), sim.max())
        edges = np.linspace(lo, hi, bins + 1)

        ax.hist(real, bins=edges, density=True, alpha=0.6, color=COR_REAL,
                edgecolor="white", label=f"Real (n={real.size})")
        ax.hist(sim, bins=edges, density=True, alpha=0.6, color=COR_SIMULADO,
                edgecolor="white", label=f"Simulado (n={sim.size})")

        if sim_params is not None:
            mu = sim_params[cond]["mu"]
            sigma = sim_params[cond]["sigma"]
            x = np.linspace(lo, hi, 300)
            pdf = stats.lognorm.pdf(x, s=sigma, scale=np.exp(mu))
            ax.plot(x, pdf, color=COR_LOGNORMAL, linewidth=1.5,
                    label=f"Lognormal (μ={mu:.2f}, σ={sigma:.3f})")

        ax.set_title(rotulo)
        ax.set_xlabel("Tempo de build (s)")
        ax.set_ylabel("Densidade (1/s)")
        ax.legend(fontsize=8)

    fig.suptitle("G1 — Tempo de build: dados reais × simulados")
    return fig
