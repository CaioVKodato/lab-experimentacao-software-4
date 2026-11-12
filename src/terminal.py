"""Ajustes da saída de terminal compartilhados pelos CLIs."""

from __future__ import annotations

import sys


def usar_utf8_na_saida() -> None:
    """
    Força UTF-8 no stdout/stderr.

    No Windows, quando a saída é redirecionada (arquivo, pipe ou outro script),
    o Python usa a página de código do sistema (cp1252), que não tem α nem H₀,
    e o print quebra com UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
