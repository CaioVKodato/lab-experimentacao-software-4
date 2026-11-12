"""t pareado e Wilcoxon pareado aplicados aos tempos de build."""

from .pareados import (
    ALPHA,
    aplicar_testes,
    p_valores,
    separar_pares,
    soma_postos_positivos,
)

__all__ = [
    "ALPHA",
    "aplicar_testes",
    "p_valores",
    "separar_pares",
    "soma_postos_positivos",
]
