"""Estimativa de parâmetros a partir dos tempos de build coletados."""

from .stats import estimate_params, outliers_iqr

__all__ = ["estimate_params", "outliers_iqr"]
