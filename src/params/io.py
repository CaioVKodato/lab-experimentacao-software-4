from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("run", "condicao", "tempo_s")


def load_builds_csv(path: Path) -> pd.DataFrame:
    """Lê o CSV da coleta e valida colunas básicas."""
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    df = pd.read_csv(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"colunas ausentes no CSV: {missing}")

    df = df.copy()
    df["condicao"] = df["condicao"].astype(str).str.strip()
    df["tempo_s"] = pd.to_numeric(df["tempo_s"], errors="raise")
    return df
