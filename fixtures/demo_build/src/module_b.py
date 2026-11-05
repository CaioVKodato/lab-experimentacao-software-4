"""Segundo módulo do build demo — um pouco mais pesado."""

ROWS = [[i * j for j in range(80)] for i in range(80)]


def work() -> int:
    return sum(sum(row) for row in ROWS)
