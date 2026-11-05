from __future__ import annotations

import argparse
from pathlib import Path

from coleta.config import DEFAULT_CSV, REPO_ROOT

from .export import write_params_json
from .io import load_builds_csv
from .stats import estimate_params

DEFAULT_PARAMS = REPO_ROOT / "data" / "params.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estima parâmetros de simulação a partir de data/builds.csv."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_CSV,
        help=f"CSV de entrada (padrão: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PARAMS,
        help=f"JSON de saída (padrão: {DEFAULT_PARAMS})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    df = load_builds_csv(args.input)
    params = estimate_params(df)
    write_params_json(args.output, params)

    sem = params["por_condicao"]["sem_cache"]
    com = params["por_condicao"]["com_cache"]
    diff = params["pareado"]["diff_sem_menos_com"]
    print(f"params gravados em {args.output}")
    print(
        f"sem_cache  n={sem['n']}  mediana={sem['median']:.4f}s  "
        f"skew={sem['skewness']:.3f}"
    )
    print(
        f"com_cache  n={com['n']}  mediana={com['median']:.4f}s  "
        f"skew={com['skewness']:.3f}"
    )
    print(
        f"diff (sem-com)  mediana={diff['median']:.4f}s  "
        f"mean={diff['mean']:.4f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
