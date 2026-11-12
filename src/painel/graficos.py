from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from testes import soma_postos_positivos

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


# mesma cor de cada teste em G2, G3 e G4
COR_TESTE = {"t pareado": "#55A868", "Wilcoxon pareado": "#8172B3"}


def _wilcoxon_nula(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Distribuição exata de W+ (soma dos postos positivos) sob H₀ com n pares."""
    max_w = n * (n + 1) // 2
    contagem = np.zeros(max_w + 1)
    contagem[0] = 1
    for posto in range(1, n + 1):
        contagem[posto:] = contagem[posto:] + contagem[:-posto].copy()
    return np.arange(max_w + 1), contagem / contagem.sum()


def _painel_t(ax: plt.Axes, diffs: np.ndarray, alpha: float) -> None:
    n = diffs.size
    gl = n - 1
    t_obs = float(stats.ttest_1samp(diffs, 0.0).statistic)
    p = float(2 * stats.t.sf(abs(t_obs), gl))
    t_crit = float(stats.t.ppf(1 - alpha / 2, gl))
    cor = COR_TESTE["t pareado"]

    lim = 4.5
    x = np.linspace(-lim, lim, 800)
    y = stats.t.pdf(x, gl)
    ax.plot(x, y, color=cor, linewidth=2, label=f"t sob H₀ (gl={gl})")

    rej = np.abs(x) >= t_crit
    ax.fill_between(x, y, where=rej, color=cor, alpha=0.25,
                    label=f"Região de rejeição (|t| ≥ {t_crit:.2f})")
    area_p = np.abs(x) >= abs(t_obs)
    ax.fill_between(x, y, where=area_p, facecolor="none", edgecolor=cor,
                    hatch="///", linewidth=0, label=f"p-valor = {p:.3g}")
    if abs(t_obs) <= lim:
        ax.axvline(t_obs, color="black", linestyle="--", linewidth=1,
                   label=f"t observado = {t_obs:.2f}")
    else:
        # fora do eixo: seta na borda em vez de achatar a curva
        borda = np.sign(t_obs) * lim
        ax.annotate(f"t observado = {t_obs:.2f}", xy=(borda, 0.02),
                    xytext=(borda * 0.55, 0.12), ha="center", fontsize=8,
                    arrowprops={"arrowstyle": "->", "color": "black"})

    ax.set_title("t pareado")
    ax.set_xlabel("Estatística t (adimensional)")
    ax.set_ylabel("Densidade")
    ax.legend(fontsize=8, loc="upper left")


def _painel_wilcoxon(ax: plt.Axes, diffs: np.ndarray, alpha: float) -> None:
    # diferenças nulas não entram no Wilcoxon, nem no n da distribuição
    n = int(np.count_nonzero(diffs))
    ws, probs = _wilcoxon_nula(n)
    centro = n * (n + 1) / 4
    w_obs = soma_postos_positivos(diffs)
    distancia = abs(w_obs - centro)
    p = float(min(1.0, probs[np.abs(ws - centro) >= distancia].sum()))

    # maior cauda inferior com P <= α/2; por simetria vale para a superior
    acum = np.cumsum(probs)
    w_crit = int(ws[acum <= alpha / 2].max())
    rej = (ws <= w_crit) | (ws >= ws.max() - w_crit)
    area_p = np.abs(ws - centro) >= distancia
    cor = COR_TESTE["Wilcoxon pareado"]

    ax.bar(ws, probs, width=1.0, color=cor, alpha=0.35, edgecolor="none",
           label=f"W⁺ sob H₀ (n={n}, exata)")
    ax.bar(ws[rej], probs[rej], width=1.0, color=cor, alpha=0.8, edgecolor="none",
           label=f"Região de rejeição (W⁺ ≤ {w_crit} ou ≥ {ws.max() - w_crit})")
    ax.bar(ws[area_p], probs[area_p], width=1.0, facecolor="none", edgecolor="black",
           hatch="///", linewidth=0, label=f"p-valor = {p:.3g}")
    ax.axvline(w_obs, color="black", linestyle="--", linewidth=1,
               label=f"W⁺ observado = {w_obs:.0f}")

    ax.set_title("Wilcoxon pareado")
    ax.set_xlabel("Soma dos postos positivos W⁺ (adimensional)")
    ax.set_ylabel("Probabilidade")
    ax.legend(fontsize=8, loc="upper left")


def fig_g2(
    sem: np.ndarray, com: np.ndarray, alpha: float = 0.05, titulo: str = ""
) -> plt.Figure:
    """
    G2: distribuição da estatística de cada teste sob H₀, com a região de
    rejeição (bicaudal, α) sombreada e o p-valor do exemplo hachurado.
    """
    diffs = np.asarray(sem, dtype=float) - np.asarray(com, dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    _painel_t(axes[0], diffs, alpha)
    _painel_wilcoxon(axes[1], diffs, alpha)
    sufixo = f" — {titulo}" if titulo else ""
    fig.suptitle(f"G2 — Estatística dos testes sob H₀ (α = {alpha}){sufixo}")
    return fig
