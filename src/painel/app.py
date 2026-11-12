from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from coleta.config import REPO_ROOT
from params.io import load_builds_csv
from simulacao import DEFAULT_SEED, gerar_pares, load_sim_params
from testes import ALPHA, aplicar_testes, separar_pares

from .graficos import fig_g1, fig_g2, fig_g3, taxas_erro_tipo_i

DATA = REPO_ROOT / "data"
REPO_URL = "https://github.com/CaioVKodato/lab-experimentacao-software-4"
PROJECT_URL = "https://github.com/users/CaioVKodato/projects/9"
DASHBOARD_URL = None  # preencher quando publicar
EFEITO_DIDATICO = 0.02  # deslocamento em log(tempo) do exemplo do G2
AREA_MINIMA_VISIVEL = 1e-3  # abaixo disso o hachurado do p-valor some no G2


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
        f"com cache aparecem só na cauda da lognormal, e numa amostra de {com.size} "
        "nem sempre são sorteados."
    )


def _exemplo_didatico(sim: dict) -> tuple[np.ndarray, np.ndarray]:
    """Pares com efeito pequeno (com cache ~2% mais rápido), para o p-valor aparecer como área."""
    sem = sim["sem_cache"]
    sim_pequeno = {
        **sim,
        "com_cache": {"mu": sem["mu"] - EFEITO_DIDATICO, "sigma": sem["sigma"]},
    }
    return separar_pares(gerar_pares(sim_pequeno, rng=np.random.default_rng(DEFAULT_SEED)))


def _leitura_do_exemplo(exemplo: str, testes_exemplo: list[dict]) -> str:
    """Frase do G2 montada a partir dos p-valores, para não ficar desatualizada."""
    if exemplo.startswith("Efeito pequeno"):
        contexto = f"No exemplo didático (efeito de {1 - np.exp(-EFEITO_DIDATICO):.0%})"
    else:
        contexto = "No conjunto simulado com o efeito do cache"

    leituras = []
    for teste in testes_exemplo:
        p = teste["p_valor"]
        if p < ALPHA:
            decisao = f"p = {p:.3g} < α, rejeita H₀"
        else:
            decisao = f"p = {p:.3g} ≥ α, não rejeita H₀"
        leituras.append(f"{teste['teste']}: {decisao}")
    frase = f"{contexto}: {'; '.join(leituras)}."

    if max(t["p_valor"] for t in testes_exemplo) < AREA_MINIMA_VISIVEL:
        frase += " A área do p-valor é tão pequena que não aparece no gráfico."
    return frase


def secao_testes(simulados: pd.DataFrame, sim: dict) -> None:
    st.header("3. Como os testes funcionam")

    exemplo = st.radio(
        "Exemplo marcado no G2",
        ("Efeito pequeno (didático)", "Simulado (efeito do cache)"),
        horizontal=True,
    )
    if exemplo.startswith("Simulado"):
        sem, com = separar_pares(simulados)
    else:
        sem, com = _exemplo_didatico(sim)
    st.pyplot(fig_g2(sem, com, ALPHA, titulo=exemplo))

    testes_exemplo = aplicar_testes(sem, com, ALPHA)["testes"]
    st.markdown(
        "O **t pareado** compara a média das diferenças (sem − com cache) com zero, "
        "escalada pelo erro padrão; sob H₀ a estatística segue uma t com n−1 graus de "
        "liberdade. O **Wilcoxon pareado** ignora o tamanho das diferenças e usa os "
        "postos: W⁺ soma os postos das diferenças positivas e, sob H₀, cada sinal é "
        "cara ou coroa, o que dá a distribuição exata do painel da direita. "
        f"Como o teste é bicaudal, a região de rejeição são as duas caudas com "
        f"{ALPHA / 2:.1%} cada. O p-valor (hachurado) é a probabilidade, supondo H₀ "
        "verdadeira, de uma estatística tão ou mais extrema que a observada. Ele não "
        "é a probabilidade de H₀ ser verdadeira. "
        + _leitura_do_exemplo(exemplo, testes_exemplo)
    )

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
                "Estatística": f"{t['nome_estatistica']} = {t['estatistica']:.4g}",
                "p-valor": f"{t['p_valor']:.3g}",
                "Rejeita H₀": "sim" if t["rejeita_h0"] else "não",
            }
            for t in res["testes"]
        ).set_index("Teste")
    )
    for t in res["testes"]:
        st.markdown(f"- {t['interpretacao']}")


def _desvio(linha: pd.Series) -> str:
    """Liberal/conservador só quando o IC 95% inteiro fica de um lado de α."""
    if linha["ic95_inf"] > linha["alpha"]:
        return "liberal"
    if linha["ic95_sup"] < linha["alpha"]:
        return "conservador"
    return "ok"


def _leitura_g3(taxas: pd.DataFrame) -> str:
    """Texto do G3 montado a partir dos CSVs, para acompanhar a simulação."""
    taxas = taxas.assign(desvio=taxas.apply(_desvio, axis=1))
    alpha = float(taxas["alpha"].iloc[0])

    partes = []
    for condicao, grupo in taxas.groupby("condicao", sort=False):
        if (grupo["desvio"] == "ok").all():
            partes.append(f"em **{condicao}** os dois ficam perto de {alpha:.0%}")
            continue
        leituras = [
            f"o {linha['teste']} "
            + ("fica perto de α" if linha["desvio"] == "ok" else f"fica **{linha['desvio']}**")
            + f" ({linha['taxa_rejeicao']:.1%})"
            for _, linha in grupo.iterrows()
        ]
        partes.append(f"em **{condicao}** (n={grupo['n'].iloc[0]}), " + " e ".join(leituras))

    distancia = (taxas["taxa_rejeicao"] - alpha).abs().groupby(taxas["teste"]).mean()
    mais_perto = distancia.idxmin()
    leitura = "; ".join(partes)
    return (
        leitura[0].upper() + leitura[1:] + ". "
        f"Na média das situações, o **{mais_perto}** fica mais perto de {alpha:.0%} "
        f"(desvio médio de {distancia[mais_perto] * 100:.1f} p.p. contra "
        f"{distancia.drop(mais_perto).iloc[0] * 100:.1f} p.p.)."
    )


def secao_erro_tipo_i() -> None:
    st.header("4. Erro tipo I")
    q1, q3 = DATA / "q1.csv", DATA / "q3.csv"
    if not (q1.exists() and q3.exists()):
        st.warning("Rode `python simular_q1.py` e `python simular_q3.py` para gerar o G3.")
        return

    taxas = taxas_erro_tipo_i(pd.read_csv(q1), pd.read_csv(q3))
    st.pyplot(fig_g3(taxas))
    st.markdown(
        "Cada barra é a proporção de p-valores < α em 10.000 conjuntos gerados com "
        "H₀ verdadeira; um teste calibrado fica dentro da faixa cinza. Um teste "
        "**liberal** rejeita mais que α (falso alarme de que o cache mudou o build); "
        "um **conservador** rejeita menos e perde poder. "
        + _leitura_g3(taxas)
    )


def secoes_pendentes() -> None:
    for titulo in (
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
    secao_testes(simulados, sim)
    secao_erro_tipo_i()
    secoes_pendentes()
