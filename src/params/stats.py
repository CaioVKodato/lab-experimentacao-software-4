from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _group_summary(values: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=float)
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "skewness": float(pd.Series(values).skew()),
    }


def _lognormal_params_from_sample(values: np.ndarray) -> dict[str, float]:
    """
    Ajusta uma lognormal pelos momentos amostrais de log(x).
    Útil pra simular tempos positivos e assimétricos.
    """
    values = np.asarray(values, dtype=float)
    if np.any(values <= 0):
        raise ValueError("tempos precisam ser > 0 para ajuste lognormal")

    log_x = np.log(values)
    mu = float(np.mean(log_x))
    sigma = float(np.std(log_x, ddof=1)) if values.size > 1 else 0.0
    return {"mu": mu, "sigma": max(sigma, 1e-9)}


def estimate_params(df: pd.DataFrame) -> dict[str, Any]:
    """Calcula resumos por condição + diferenças pareadas + params de simulação."""
    expected = {"sem_cache", "com_cache"}
    found = set(df["condicao"].unique())
    if not expected.issubset(found):
        raise ValueError(f"condições esperadas {expected}, encontradas {found}")

    sem = df.loc[df["condicao"] == "sem_cache"].sort_values("run")
    com = df.loc[df["condicao"] == "com_cache"].sort_values("run")

    if not sem["run"].to_numpy().tolist() == com["run"].to_numpy().tolist():
        raise ValueError("runs de sem_cache e com_cache não formam pares alinhados")

    sem_vals = sem["tempo_s"].to_numpy(dtype=float)
    com_vals = com["tempo_s"].to_numpy(dtype=float)
    diffs = sem_vals - com_vals  # positivo => cache reduziu o tempo

    return {
        "unidade": "segundos",
        "por_condicao": {
            "sem_cache": {
                **_group_summary(sem_vals),
                "lognormal": _lognormal_params_from_sample(sem_vals),
            },
            "com_cache": {
                **_group_summary(com_vals),
                "lognormal": _lognormal_params_from_sample(com_vals),
            },
        },
        "pareado": {
            "n_pares": int(diffs.size),
            "diff_sem_menos_com": _group_summary(diffs),
            "efeito_relativo_mediano": float(
                np.median(diffs) / np.median(sem_vals)
            ),
        },
        "simulacao": {
            "distribuicao": "lognormal",
            "n_por_grupo": int(diffs.size),
            "sem_cache": _lognormal_params_from_sample(sem_vals),
            "com_cache": _lognormal_params_from_sample(com_vals),
            "nota": (
                "Parâmetros mu/sigma estimados em log(tempo_s) a partir "
                "dos dados reais de data/builds.csv."
            ),
        },
    }
