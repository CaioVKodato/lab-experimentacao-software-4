"""Terceiro módulo — texto e hashing leve."""

TEXT = ("lab04-build-cache-" * 400) + "fim"


def work() -> int:
    return sum(ord(ch) for ch in TEXT) % 10_007
