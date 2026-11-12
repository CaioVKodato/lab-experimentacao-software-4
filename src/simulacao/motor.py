from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np

from testes import ALPHA, p_valores

from .gerador import DEFAULT_SEED

REPETICOES = 10_000
TESTES = ("t pareado", "Wilcoxon pareado")
Z_95 = 1.959963984540054


@dataclass(frozen=True)
class Cenario:
    """
    Uma condição da simulação.

    efeito: redução relativa do tempo com cache (0.05 = builds 5% mais rápidos);
    0 deixa H₀ verdadeira. tipo: chave de GERADORES (forma dos dados).
    """

    nome: str
    n: int
    efeito: float = 0.0
    tipo: str = "lognormal"


# (rng, sim, repetições, n) -> (sem, com) sem efeito, cada um (repetições, n).
# sem e com vêm da MESMA distribuição: a diferença fica simétrica em torno de
# zero e H₀ vale para os dois testes (média e mediana das diferenças = 0).
Gerador = Callable[[np.random.Generator, dict[str, Any], int, int], tuple[np.ndarray, np.ndarray]]


def _lognormal_base(
    rng: np.random.Generator, sim: dict[str, Any], repeticoes: int, n: int
) -> tuple[np.ndarray, np.ndarray]:
    """Os dois tempos com a lognormal do build sem cache (params.json)."""
    mu = sim["sem_cache"]["mu"]
    sigma = sim["sem_cache"]["sigma"]
    sem = rng.lognormal(mu, sigma, size=(repeticoes, n))
    com = rng.lognormal(mu, sigma, size=(repeticoes, n))
    return sem, com


PROB_OUTLIER = 0.05
FATOR_OUTLIER = 3.0


def _lognormal_outliers(
    rng: np.random.Generator, sim: dict[str, Any], repeticoes: int, n: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Base lognormal + outliers: em PROB_OUTLIER dos pares, um dos dois builds
    (sorteado, 50/50) demora FATOR_OUTLIER vezes mais.

    O lado é sorteado para a diferença continuar simétrica em torno de zero:
    H₀ segue verdadeira para os dois testes, só a normalidade quebra.
    """
    sem, com = _lognormal_base(rng, sim, repeticoes, n)
    outlier = rng.random((repeticoes, n)) < PROB_OUTLIER
    no_sem = rng.random((repeticoes, n)) < 0.5
    sem = np.where(outlier & no_sem, sem * FATOR_OUTLIER, sem)
    com = np.where(outlier & ~no_sem, com * FATOR_OUTLIER, com)
    return sem, com


# formas dos dados; Q3 usa "outliers" para violar a normalidade das diferenças
GERADORES: dict[str, Gerador] = {
    "lognormal": _lognormal_base,
    "outliers": _lognormal_outliers,
}


def intervalo_wilson(rejeicoes: int, repeticoes: int) -> tuple[float, float]:
    """IC de 95% (Wilson) para uma proporção; ~±0,43 p.p. em 5% com 10.000 repetições."""
    p = rejeicoes / repeticoes
    z2 = Z_95**2
    centro = (p + z2 / (2 * repeticoes)) / (1 + z2 / repeticoes)
    meia = (
        Z_95
        * np.sqrt(p * (1 - p) / repeticoes + z2 / (4 * repeticoes**2))
        / (1 + z2 / repeticoes)
    )
    return float(centro - meia), float(centro + meia)


def simular_cenario(
    cenario: Cenario,
    sim: dict[str, Any],
    repeticoes: int = REPETICOES,
    alpha: float = ALPHA,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    """
    Gera `repeticoes` conjuntos pareados do cenário, aplica os dois testes em
    cada um e devolve uma linha por teste com a taxa de rejeição e o IC 95%.

    Mesma semente em todo cenário: os testes veem os mesmos dados, e o
    resultado de um cenário não depende da ordem em que os outros rodaram.
    """
    if cenario.tipo not in GERADORES:
        raise ValueError(f"tipo desconhecido: {cenario.tipo} (opções: {sorted(GERADORES)})")
    if not 0 <= cenario.efeito < 1:
        raise ValueError("efeito é uma redução relativa em [0, 1)")
    if cenario.n < 2:
        raise ValueError("n precisa ser >= 2")

    rng = np.random.default_rng(seed)
    sem, com = GERADORES[cenario.tipo](rng, sim, repeticoes, cenario.n)
    com = com * (1 - cenario.efeito)

    linhas = []
    for teste, p in zip(TESTES, p_valores(sem, com)):
        rejeicoes = int(np.sum(p < alpha))
        ic_inf, ic_sup = intervalo_wilson(rejeicoes, repeticoes)
        linhas.append(
            {
                **asdict(cenario),
                "teste": teste,
                "repeticoes": repeticoes,
                "rejeicoes": rejeicoes,
                "taxa_rejeicao": rejeicoes / repeticoes,
                "ic95_inf": ic_inf,
                "ic95_sup": ic_sup,
                "alpha": alpha,
                "seed": seed,
            }
        )
    return linhas
