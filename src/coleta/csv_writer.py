from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


FIELDNAMES = ("run", "condicao", "tempo_s")


def write_builds_csv(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "run": row["run"],
                    "condicao": row["condicao"],
                    "tempo_s": f"{row['tempo_s']:.6f}",
                }
            )
