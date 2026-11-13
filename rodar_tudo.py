"""
Roda o projeto do início ao fim com um único comando: python rodar_tudo.py

Etapas (as mesmas dos scripts separados, na ordem em que uma usa a saída da outra):
  1. parâmetros a partir de data/builds.csv      → data/params.json
  2. conjunto simulado (semente 42)               → data/simulado.csv
  3. testes no simulado e nos dados reais         → data/testes_simulado.json, data/testes_reais.json
  4. Q1, Q2 e Q3 (10.000 repetições, semente 42)  → data/q1.csv, data/q2.csv, data/q3.csv

A coleta (coletar_builds.py) fica de fora por padrão: ela mede tempos reais, que mudam
com a máquina, e trocaria os dados de todo o trabalho. Use --coletar só para recoletar.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from coleta.cli import main as coletar  # noqa: E402
from params.cli import main as estimar_params  # noqa: E402
from simulacao.cli import main as simular_dados  # noqa: E402
from simulacao.q1 import main as simular_q1  # noqa: E402
from simulacao.q2 import main as simular_q2  # noqa: E402
from simulacao.q3 import main as simular_q3  # noqa: E402
from terminal import usar_utf8_na_saida  # noqa: E402
from testes.cli import main as testar  # noqa: E402

DATA = ROOT / "data"

Etapa = tuple[str, Callable[[list[str]], int], list[str]]

ETAPAS: list[Etapa] = [
    ("Parâmetros da simulação", estimar_params, []),
    ("Conjunto simulado", simular_dados, []),
    ("Testes no conjunto simulado", testar, []),
    ("Testes nos dados reais", testar,
     ["--input", str(DATA / "builds.csv"), "--output", str(DATA / "testes_reais.json")]),
    ("Q1: erro tipo I", simular_q1, []),
    ("Q2: poder", simular_q2, []),
    ("Q3: violação dos pressupostos", simular_q3, []),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Roda o Lab 04 do início ao fim (semente 42).")
    parser.add_argument(
        "--coletar",
        action="store_true",
        help="recoleta os tempos de build antes de tudo (muda os dados reais e todos os resultados)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="abre o dashboard (streamlit run dashboard.py) no fim",
    )
    return parser


def rodar_etapa(numero: int, total: int, nome: str, funcao: Callable[[list[str]], int], argv: list[str]) -> None:
    print(f"\n[{numero}/{total}] {nome}")
    inicio = time.perf_counter()
    codigo = funcao(argv)
    if codigo != 0:
        raise SystemExit(f"Etapa '{nome}' terminou com código {codigo}.")
    print(f"      ok ({time.perf_counter() - inicio:.1f} s)")


def main(argv: list[str] | None = None) -> int:
    usar_utf8_na_saida()
    args = build_parser().parse_args(argv)

    etapas = list(ETAPAS)
    if args.coletar:
        etapas.insert(0, ("Coleta dos tempos de build", coletar, []))

    for numero, (nome, funcao, argumentos) in enumerate(etapas, start=1):
        rodar_etapa(numero, len(etapas), nome, funcao, argumentos)

    print("\nPronto: arquivos de data/ atualizados.")
    if args.dashboard:
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "dashboard.py")])
    print("Para abrir o dashboard: streamlit run dashboard.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
