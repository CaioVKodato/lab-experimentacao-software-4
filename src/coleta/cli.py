from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import CollectConfig, DEFAULT_CSV, DEFAULT_N_PAIRS, DEMO_BUILD
from .runner import collect_build_times


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Coleta tempos de build com e sem cache (Lab 04)."
    )
    parser.add_argument(
        "--n-pairs",
        type=int,
        default=DEFAULT_N_PAIRS,
        help=f"quantidade de pares (sem_cache + com_cache). padrão: {DEFAULT_N_PAIRS}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CSV,
        help=f"CSV de saída (padrão: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=DEMO_BUILD,
        help=f"pasta do projeto com build.py (padrão: {DEMO_BUILD})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CollectConfig(
        project_dir=args.project_dir,
        output_csv=args.output,
        n_pairs=args.n_pairs,
        python_exe=sys.executable,
    )
    rows = collect_build_times(config)
    print(f"\n{len(rows)} linhas gravadas em {config.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
