"""Tamanho de efeito de cada teste pareado, em unidade padronizada e em segundos."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats

NIVEL_CONFIANCA = 0.95


def efeito_t_pareado(sem: np.ndarray, com: np.ndarray) -> dict[str, Any]:
    """
    Efeito na escala do t pareado (média das diferenças D = sem − com).

    d_z = média(D) / desvio(D): quantos desvios das diferenças o cache move
    o tempo (0,2 pequeno, 0,5 médio, 0,8 grande, pela convenção de Cohen).
    O IC 95% da média de D dá o mesmo efeito em segundos.
    """
    sem = np.asarray(sem, dtype=float)
    diffs = sem - np.asarray(com, dtype=float)
    media = float(np.mean(diffs))
    desvio = float(np.std(diffs, ddof=1))
    erro_padrao = desvio / np.sqrt(diffs.size)
    margem = float(stats.t.ppf((1 + NIVEL_CONFIANCA) / 2, diffs.size - 1) * erro_padrao)
    return {
        "d_z": media / desvio,
        "diferenca_media_s": media,
        "ic95_diferenca_media_s": [media - margem, media + margem],
        "reducao_relativa_media": media / float(np.mean(sem)),
    }


def hodges_lehmann(diffs: np.ndarray) -> float:
    """
    Estimador de Hodges-Lehmann: mediana das médias de Walsh (d_i + d_j) / 2, i ≤ j.

    É o "centro" que o Wilcoxon pareado estima, assim como a média é o do t.
    """
    diffs = np.asarray(diffs, dtype=float)
    i, j = np.triu_indices(diffs.size)
    return float(np.median((diffs[i] + diffs[j]) / 2))


def efeito_wilcoxon_pareado(sem: np.ndarray, com: np.ndarray) -> dict[str, Any]:
    """
    Efeito na escala do Wilcoxon pareado (postos das diferenças).

    r rank-biserial = (W⁺ − W⁻) / (W⁺ + W⁻): vai de −1 (todas as diferenças
    negativas) a +1 (todas positivas); 0 é o que H₀ espera.
    """
    sem = np.asarray(sem, dtype=float)
    diffs = sem - np.asarray(com, dtype=float)
    nao_nulas = diffs[diffs != 0]
    postos = stats.rankdata(np.abs(nao_nulas))
    w_mais = float(postos[nao_nulas > 0].sum())
    w_menos = float(postos[nao_nulas < 0].sum())
    total = w_mais + w_menos
    mediana = float(np.median(diffs))
    return {
        "r_rank_biserial": (w_mais - w_menos) / total if total else 0.0,
        "diferenca_mediana_s": mediana,
        "hodges_lehmann_s": hodges_lehmann(diffs),
        "reducao_relativa_mediana": mediana / float(np.median(sem)),
    }
