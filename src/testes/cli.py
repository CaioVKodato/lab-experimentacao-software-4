from __future__ import annotations

import argparse
import json
from pathlib import Path

from coleta.config import REPO_ROOT
from params.io import load_builds_csv
from terminal import usar_utf8_na_saida

from .pareados import ALPHA, aplicar_testes, separar_pares

DEFAULT_INPUT = REPO_ROOT / "data" / "simulado.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "testes_simulado.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aplica t pareado e Wilcoxon pareado num CSV de pares."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"CSV de entrada (padrão: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSON de saída (padrão: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=ALPHA,
        help=f"nível de significância (padrão: {ALPHA})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    usar_utf8_na_saida()
    args = build_parser().parse_args(argv)
    sem, com = separar_pares(load_builds_csv(args.input))
    resultado = aplicar_testes(sem, com, alpha=args.alpha)
    resultado = {"fonte": args.input.name, **resultado}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    diff = resultado["diff_sem_menos_com"]
    print(f"resultado gravado em {args.output}")
    print(
        f"{resultado['n_pares']} pares  diff (sem-com)  "
        f"média={diff['mean']:.4f}s  mediana={diff['median']:.4f}s"
    )
    for teste in resultado["testes"]:
        print(
            f"{teste['teste']:<17} {teste['nome_estatistica']}={teste['estatistica']:.4g}  "
            f"p={teste['p_valor']:.4g}"
        )
        print(f"  {teste['interpretacao']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
