from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from coleta.config import REPO_ROOT
from terminal import usar_utf8_na_saida
from testes import ALPHA

from .gerador import DEFAULT_SEED, load_sim_params
from .motor import REPETICOES, Cenario, simular_cenario

DEFAULT_PARAMS = REPO_ROOT / "data" / "params.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "q1.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Q1: erro tipo I do t pareado e do Wilcoxon com H₀ verdadeira."
    )
    parser.add_argument("--params", type=Path, default=DEFAULT_PARAMS,
                        help=f"JSON de parâmetros (padrão: {DEFAULT_PARAMS})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"CSV de saída (padrão: {DEFAULT_OUTPUT})")
    parser.add_argument("--repeticoes", type=int, default=REPETICOES,
                        help=f"conjuntos simulados (padrão: {REPETICOES})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"semente do gerador (padrão: {DEFAULT_SEED})")
    parser.add_argument("--alpha", type=float, default=ALPHA,
                        help=f"nível de significância (padrão: {ALPHA})")
    return parser


def main(argv: list[str] | None = None) -> int:
    usar_utf8_na_saida()
    args = build_parser().parse_args(argv)
    sim = load_sim_params(args.params)

    cenario = Cenario(nome="base", n=int(sim["n_por_grupo"]), efeito=0.0)
    linhas = simular_cenario(
        cenario, sim, repeticoes=args.repeticoes, alpha=args.alpha, seed=args.seed
    )
    df = pd.DataFrame(linhas)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, float_format="%.6f")

    print(f"Q1 gravado em {args.output} (seed={args.seed}, {args.repeticoes} repetições)")
    print(f"cenário {cenario.nome}: n={cenario.n}  efeito=0 (H₀ verdadeira)  α={args.alpha}")
    for linha in linhas:
        print(
            f"{linha['teste']:<17} erro tipo I = {linha['taxa_rejeicao']:.2%}  "
            f"IC95% [{linha['ic95_inf']:.2%}, {linha['ic95_sup']:.2%}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
