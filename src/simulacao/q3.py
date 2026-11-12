from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from coleta.config import REPO_ROOT
from terminal import usar_utf8_na_saida
from testes import ALPHA

from .gerador import DEFAULT_SEED, load_sim_params
from .motor import REPETICOES, TESTES, Cenario, simular_cenario
from .q2 import EFEITOS

DEFAULT_PARAMS = REPO_ROOT / "data" / "params.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "q3.csv"
# com n = 8 o poder sobe mais devagar; 15% e 20% fecham a curva
EFEITOS_Q3 = (*EFEITOS, 0.15, 0.20)


def condicoes(n_base: int) -> list[tuple[str, int, str]]:
    """(condição, n, tipo). A base entra junto para G3/G4 lerem um arquivo só."""
    return [
        ("base", n_base, "lognormal"),
        ("outliers", n_base, "outliers"),
        ("amostra pequena", 8, "lognormal"),
        ("amostra pequena + outliers", 8, "outliers"),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Q3: erro tipo I e poder quando os dados violam os pressupostos do t."
    )
    parser.add_argument("--params", type=Path, default=DEFAULT_PARAMS,
                        help=f"JSON de parâmetros (padrão: {DEFAULT_PARAMS})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"CSV de saída (padrão: {DEFAULT_OUTPUT})")
    parser.add_argument("--efeitos", type=float, nargs="+", default=list(EFEITOS_Q3),
                        help="reduções relativas a simular (padrão: %(default)s)")
    parser.add_argument("--repeticoes", type=int, default=REPETICOES,
                        help=f"conjuntos simulados por efeito (padrão: {REPETICOES})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"semente do gerador (padrão: {DEFAULT_SEED})")
    parser.add_argument("--alpha", type=float, default=ALPHA,
                        help=f"nível de significância (padrão: {ALPHA})")
    return parser


def main(argv: list[str] | None = None) -> int:
    usar_utf8_na_saida()
    args = build_parser().parse_args(argv)
    sim = load_sim_params(args.params)

    linhas = []
    for condicao, n, tipo in condicoes(int(sim["n_por_grupo"])):
        for efeito in args.efeitos:
            cenario = Cenario(nome=condicao, n=n, efeito=efeito, tipo=tipo)
            linhas.extend(
                simular_cenario(
                    cenario, sim, repeticoes=args.repeticoes, alpha=args.alpha, seed=args.seed
                )
            )
    df = pd.DataFrame(linhas).rename(columns={"nome": "condicao"})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, float_format="%.6f")

    print(f"Q3 gravado em {args.output} (seed={args.seed}, {args.repeticoes} repetições por efeito)")
    for (condicao, n), grupo in df.groupby(["condicao", "n"], sort=False):
        tabela = grupo.pivot(index="efeito", columns="teste", values="taxa_rejeicao")[list(TESTES)]
        print(f"\n{condicao} (n={n})")
        for efeito, linha in tabela.iterrows():
            taxas = "  ".join(f"{teste} = {taxa:.1%}" for teste, taxa in linha.items())
            print(f"  efeito {efeito:>4.0%}  {taxas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
