from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from coleta.config import REPO_ROOT
from params.io import load_builds_csv
from simulacao import load_sim_params

from .graficos import fig_g1

DATA = REPO_ROOT / "data"
REPO_URL = "https://github.com/CaioVKodato/lab-experimentacao-software-4"
PROJECT_URL = "https://github.com/users/CaioVKodato/projects/9"
DASHBOARD_URL = None  # preencher quando publicar


def _resumo(df: pd.DataFrame, cond: str) -> pd.Series:
    return df.loc[df["condicao"] == cond, "tempo_s"]


def secao_links() -> None:
    dashboard = f"[Dashboard]({DASHBOARD_URL})" if DASHBOARD_URL else "Dashboard: *(a publicar)*"
    st.markdown(
        f"[Repositório]({REPO_URL}) · [GitHub Projects]({PROJECT_URL}) · {dashboard}"
    )


def secao_cenario(reais: pd.DataFrame) -> None:
    st.header("1. Cenário")
    n_pares = reais["run"].nunique()
    st.markdown(
        "**Pergunta:** o cache reduz o tempo de build do projeto demo?\n\n"
        "- **H₀:** a diferença de tempo (sem cache − com cache) é zero; "
        "o cache não muda o tempo de build.\n"
        "- **H₁:** a diferença é diferente de zero (bicaudal).\n\n"
        "Testes comparados: **t pareado** × **Wilcoxon pareado**.\n\n"
        f"Dados reais: {n_pares} pares de builds do projeto `fixtures/demo_build/`, "
        "rodados na mesma máquina com e sem cache (`python coletar_builds.py`)."
    )


def secao_dados(reais: pd.DataFrame, simulados: pd.DataFrame, sim: dict) -> None:
    st.header("2. Os dados")
    st.pyplot(fig_g1(reais, simulados, sim))

    sem, com = _resumo(reais, "sem_cache"), _resumo(reais, "com_cache")
    st.markdown(
        f"Os tempos reais são positivos e assimétricos à direita: sem cache a mediana "
        f"é {sem.median():.3f} s (assimetria {sem.skew():.2f}) e com cache cai para "
        f"{com.median():.3f} s (assimetria {com.skew():.2f}), com mais dispersão e "
        "alguns builds lentos. Por isso cada condição é simulada com uma lognormal, "
        "com μ e σ estimados em log(tempo) a partir dos dados reais "
        f"(`data/params.json`), e o mesmo n={com.size} pares da coleta. "
        "O simulado cobre a mesma faixa e o centro das reais; os builds lentos "
        "com cache aparecem só na cauda da lognormal, e numa amostra de 15 "
        "nem sempre são sorteados."
    )


def secao_testes() -> None:
    st.header("3. Como os testes funcionam")
    st.info("G2 — distribuição da estatística sob H₀ (Issue #6).")

    path = DATA / "testes_simulado.json"
    if not path.exists():
        st.warning("Rode `python testar_simulado.py` para gerar o resultado.")
        return

    res = json.loads(path.read_text(encoding="utf-8"))
    st.markdown(
        f"Resultado dos dois testes no conjunto simulado "
        f"({res['n_pares']} pares, {res['alternativa']}, α = {res['alpha']}):"
    )
    st.table(
        pd.DataFrame(
            {
                "Teste": t["teste"],
                "Estatística": f"{t['nome_estatistica']} = {t['estatistica']:.3f}",
                "p-valor": f"{t['p_valor']:.3g}",
                "Rejeita H₀": "sim" if t["rejeita_h0"] else "não",
            }
            for t in res["testes"]
        ).set_index("Teste")
    )
    for t in res["testes"]:
        st.markdown(f"- {t['interpretacao']}")


def secoes_pendentes() -> None:
    for titulo in (
        "4. Erro tipo I",
        "5. Poder",
        "6. Dados reais",
        "7. Conclusão",
    ):
        st.header(titulo)
        st.caption("Sprint 2.")


def main() -> None:
    st.set_page_config(page_title="Lab 04 — Cache × tempo de build", layout="wide")
    st.title("Lab 04 — t pareado × Wilcoxon pareado")
    secao_links()

    reais = load_builds_csv(DATA / "builds.csv")
    simulados = load_builds_csv(DATA / "simulado.csv")
    sim = load_sim_params(DATA / "params.json")

    secao_cenario(reais)
    secao_dados(reais, simulados, sim)
    secao_testes()
    secoes_pendentes()
