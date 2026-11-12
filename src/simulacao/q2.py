from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from coleta.config import REPO_ROOT
from terminal import usar_utf8_na_saida
from testes import ALPHA

from .gerador import DEFAULT_SEED, load_sim_params
from .motor import REPETICOES, TESTES, Cenario, simular_cenario

DEFAULT_PARAMS = REPO_ROOT / "data" / "params.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "q2.csv"
# redução relativa do tempo com cache; o efeito real (~50%) já dá poder 100%,
# então a grade fica onde a curva sai de 5% e chega perto de 100%
EFEITOS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Q2: poder do t pareado e do Wilcoxon com efeitos crescentes."
    )
    parser.add_argument("--params", type=Path, default=DEFAULT_PARAMS,
                        help=f"JSON de parâmetros (padrão: {DEFAULT_PARAMS})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"CSV de saída (padrão: {DEFAULT_OUTPUT})")
    parser.add_argument("--efeitos", type=float, nargs="+", default=list(EFEITOS),
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
    n = int(sim["n_por_grupo"])

    linhas = []
    for efeito in args.efeitos:
        cenario = Cenario(nome="base", n=n, efeito=efeito)
        linhas.extend(
            simular_cenario(
                cenario, sim, repeticoes=args.repeticoes, alpha=args.alpha, seed=args.seed
            )
        )
    df = pd.DataFrame(linhas)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, float_format="%.6f")

    print(f"Q2 gravado em {args.output} (seed={args.seed}, {args.repeticoes} repetições por efeito)")
    print(f"cenário base: n={n}  α={args.alpha}")
    tabela = df.pivot(index="efeito", columns="teste", values="taxa_rejeicao")[list(TESTES)]
    for efeito, linha in tabela.iterrows():
        taxas = "  ".join(f"{teste} = {taxa:.1%}" for teste, taxa in linha.items())
        print(f"efeito {efeito:>4.0%}  {taxas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
