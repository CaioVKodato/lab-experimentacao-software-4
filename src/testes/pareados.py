from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05


def separar_pares(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Devolve (sem_cache, com_cache) alinhados por run."""
    sem = df.loc[df["condicao"] == "sem_cache"].sort_values("run")
    com = df.loc[df["condicao"] == "com_cache"].sort_values("run")

    if sem.empty or com.empty:
        raise ValueError("CSV precisa ter as condições sem_cache e com_cache")
    if not sem["run"].to_numpy().tolist() == com["run"].to_numpy().tolist():
        raise ValueError("runs de sem_cache e com_cache não formam pares alinhados")

    return (
        sem["tempo_s"].to_numpy(dtype=float),
        com["tempo_s"].to_numpy(dtype=float),
    )


def soma_postos_positivos(diffs: np.ndarray) -> float:
    """
    W⁺ do Wilcoxon pareado: soma dos postos de |d| das diferenças positivas.

    Diferenças iguais a zero saem antes de ordenar, como no scipy
    (zero_method="wilcox"). O scipy devolve min(W⁺, W⁻) no teste bicaudal,
    que dá o mesmo p-valor; aqui usamos W⁺ porque é ele que o G2 mostra.
    """
    diffs = np.asarray(diffs, dtype=float)
    nao_nulas = diffs[diffs != 0]
    postos = stats.rankdata(np.abs(nao_nulas))
    return float(postos[nao_nulas > 0].sum())


def p_valores(sem: np.ndarray, com: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    p-valores bicaudais (t pareado, Wilcoxon pareado) linha a linha.

    sem/com com forma (repetições, n). Usa as mesmas chamadas do scipy que
    aplicar_testes, só que vetorizadas — p-valores idênticos, ~200× mais rápido
    nas 10.000 repetições da simulação.
    """
    sem = np.asarray(sem, dtype=float)
    com = np.asarray(com, dtype=float)
    p_t = stats.ttest_rel(sem, com, axis=-1, alternative="two-sided").pvalue
    p_w = stats.wilcoxon(sem, com, axis=-1, alternative="two-sided").pvalue
    return np.asarray(p_t), np.asarray(p_w)


def _interpretar(nome: str, p_valor: float, alpha: float, diff: float) -> str:
    if p_valor < alpha:
        sentido = "reduz" if diff > 0 else "aumenta"
        return (
            f"{nome}: p = {p_valor:.4g} < α = {alpha}. Rejeitamos H₀: "
            f"há evidência de que o cache {sentido} o tempo de build."
        )
    return (
        f"{nome}: p = {p_valor:.4g} ≥ α = {alpha}. Não rejeitamos H₀: "
        "não há evidência de diferença no tempo de build com o cache."
    )


def aplicar_testes(
    sem: np.ndarray, com: np.ndarray, alpha: float = ALPHA
) -> dict[str, Any]:
    """
    Aplica t pareado e Wilcoxon pareado (bicaudais) em sem − com.

    t pareado compara a média das diferenças com zero;
    Wilcoxon compara os postos das diferenças (mediana) com zero e
    reporta W⁺ como estatística.
    """
    sem = np.asarray(sem, dtype=float)
    com = np.asarray(com, dtype=float)
    diffs = sem - com  # positivo => cache reduziu o tempo

    t = stats.ttest_rel(sem, com, alternative="two-sided")
    w = stats.wilcoxon(sem, com, alternative="two-sided")

    resultados = []
    for nome, estatistica, nome_estat, p_valor, centro in (
        ("t pareado", t.statistic, "t", t.pvalue, np.mean(diffs)),
        ("Wilcoxon pareado", soma_postos_positivos(diffs), "W⁺", w.pvalue, np.median(diffs)),
    ):
        p_valor = float(p_valor)
        resultados.append(
            {
                "teste": nome,
                "estatistica": float(estatistica),
                "nome_estatistica": nome_estat,
                "p_valor": p_valor,
                "rejeita_h0": bool(p_valor < alpha),
                "interpretacao": _interpretar(nome, p_valor, alpha, centro),
            }
        )

    return {
        "alpha": alpha,
        "alternativa": "bicaudal",
        "n_pares": int(diffs.size),
        "diff_sem_menos_com": {
            "mean": float(np.mean(diffs)),
            "median": float(np.median(diffs)),
        },
        "graus_liberdade_t": int(diffs.size - 1),
        "testes": resultados,
    }
