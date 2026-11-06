from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from coleta.config import REPO_ROOT

from .gerador import DEFAULT_SEED, gerar_pares, load_sim_params

DEFAULT_PARAMS = REPO_ROOT / "data" / "params.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "simulado.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera pares simulados (sem/com cache) a partir de data/params.json."
    )
    parser.add_argument(
        "--params",
        type=Path,
        default=DEFAULT_PARAMS,
        help=f"JSON de parâmetros (padrão: {DEFAULT_PARAMS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"CSV de saída (padrão: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="nº de pares (padrão: n_por_grupo do params.json)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"semente do gerador (padrão: {DEFAULT_SEED})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sim = load_sim_params(args.params)
    df = gerar_pares(sim, n=args.n, rng=np.random.default_rng(args.seed))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, float_format="%.6f")

    print(f"simulado gravado em {args.output} (seed={args.seed})")
    for cond, grupo in df.groupby("condicao", sort=False):
        vals = grupo["tempo_s"]
        print(
            f"{cond:<10} n={vals.size}  mediana={vals.median():.4f}s  "
            f"skew={vals.skew():.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
