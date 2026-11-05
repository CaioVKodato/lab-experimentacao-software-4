"""Módulo de exemplo processado pelo build demo."""

DATA = list(range(2_000))


def work() -> int:
    total = 0
    for value in DATA:
        total += value * value
    return total
