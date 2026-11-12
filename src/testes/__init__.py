"""t pareado e Wilcoxon pareado aplicados aos tempos de build."""

from .efeito import efeito_t_pareado, efeito_wilcoxon_pareado, hodges_lehmann
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
    "efeito_t_pareado",
    "efeito_wilcoxon_pareado",
    "hodges_lehmann",
    "p_valores",
    "separar_pares",
    "soma_postos_positivos",
]
