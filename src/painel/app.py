from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from coleta.config import REPO_ROOT
from params import outliers_iqr
from params.io import load_builds_csv
from simulacao import DEFAULT_SEED, gerar_pares, load_sim_params
from testes import ALPHA, aplicar_testes, separar_pares

from .graficos import (
    curvas_poder,
    efeito_para_poder,
    fig_g1,
    fig_g2,
    fig_g3,
    fig_g4,
    taxas_erro_tipo_i,
)

DATA = REPO_ROOT / "data"
REPO_URL = "https://github.com/CaioVKodato/lab-experimentacao-software-4"
PROJECT_URL = "https://github.com/users/CaioVKodato/projects/9"
EFEITO_DIDATICO = 0.02  # deslocamento em log(tempo) do exemplo do G2
AREA_MINIMA_VISIVEL = 1e-3  # abaixo disso o hachurado do p-valor some no G2


def _resumo(df: pd.DataFrame, cond: str) -> pd.Series:
    return df.loc[df["condicao"] == cond, "tempo_s"]


def secao_links() -> None:
    st.markdown(f"[Repositório]({REPO_URL}) · [GitHub Projects]({PROJECT_URL})")


def secao_cenario(reais: pd.DataFrame) -> None:
    st.header("1. Cenário")
    n_pares = reais["run"].nunique()
    st.markdown(
        "**Pergunta:** ativar o cache muda o tempo de build do projeto demo?\n\n"
        "Em cada par *i*, medimos o mesmo build sem e com cache e olhamos a diferença "
        r"$D_i = T_{\text{sem},i} - T_{\text{com},i}$ (em segundos; positiva quando "
        "o cache deixa o build mais rápido). Testes comparados: **t pareado** × "
        "**Wilcoxon pareado**, com α = 0,05.\n\n"
        "| Teste | H₀ | H₁ |\n"
        "|---|---|---|\n"
        r"| t pareado | $\mu_D = 0$: em média, ligar o cache não muda o tempo de build "
        r"| $\mu_D \neq 0$: em média, o tempo muda (para menos ou para mais) |"
        "\n"
        r"| Wilcoxon pareado | $D$ simétrica em torno de 0 (mediana $= 0$): ganhar ou "
        "perder tempo com o cache é igualmente provável "
        r"| $D$ deslocada de 0 (mediana $\neq 0$): o cache tende a acelerar ou a atrasar "
        "o build |\n\n"
        "Os dois testes são **bicaudais** (2,5% de α em cada cauda). Antes de medir, não "
        "dava para descartar que o cache deixasse o build mais lento: com ele ligado, o "
        "build lê e grava artefatos e o manifesto em disco, um custo que pode superar a "
        "economia. O bicaudal detecta efeito nos dois sentidos e o sinal de D diz depois "
        "para que lado o cache mexeu.\n\n"
        f"**Dados reais:** {n_pares} pares ({2 * n_pares} builds) do projeto "
        "`fixtures/demo_build/`, medidos na mesma máquina, alternando sem e com cache "
        f"(`python coletar_builds.py`). Registro da coleta em [data/README.md]({REPO_URL}/blob/main/data/README.md)."
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
        "nem sempre são sorteados. " + _leitura_outliers(reais)
    )


def _leitura_outliers(reais: pd.DataFrame) -> str:
    """Frase com os outliers de cada condição pela regra de 1,5·IQR."""
    partes = []
    for cond, rotulo in (("sem_cache", "sem cache"), ("com_cache", "com cache")):
        builds = outliers_iqr(reais.loc[reais["condicao"] == cond])["builds"]
        if not builds:
            partes.append(f"nenhum {rotulo}")
            continue
        lista = " e ".join(f"run {b['run']} com {b['tempo_s']:.3f} s" for b in builds)
        plural = "outlier" if len(builds) == 1 else "outliers"
        partes.append(f"{len(builds)} {plural} {rotulo} ({lista})")
    # quem tem outlier aparece primeiro: "2 outliers com cache (...) e nenhum sem cache"
    partes.sort(key=lambda parte: parte.startswith("nenhum"))
    return f"Pela regra de 1,5·IQR (a do boxplot), há {' e '.join(partes)}."


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
    frase = f"{contexto}: {'; '.join(leituras)}"

    if max(t["p_valor"] for t in testes_exemplo) < AREA_MINIMA_VISIVEL:
        frase += " (a área do p-valor é tão pequena que não aparece no gráfico)"
    return frase + "."


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
        "O **t pareado** compara a média das diferenças (sem − com cache) com zero e, "
        "sob H₀, segue uma t com n−1 graus de liberdade; o **Wilcoxon pareado** usa só "
        "os postos (W⁺ soma os postos das diferenças positivas) e, sob H₀, cada sinal é "
        "cara ou coroa, o que dá a distribuição exata da direita. "
        f"Como o teste é bicaudal, a região de rejeição são as duas caudas sombreadas, "
        f"com {ALPHA / 2:.1%} cada. O p-valor (hachurado) é a probabilidade, supondo H₀ "
        "verdadeira, de uma estatística tão ou mais extrema que a observada, e não a "
        "probabilidade de H₀ ser verdadeira. "
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


PODER_ALVO = 0.8
EMPATE_PP = 1.0  # diferença de poder abaixo disso (p.p.) conta como empate


TESTES = ("t pareado", "Wilcoxon pareado")


def resumo_poder(curvas: pd.DataFrame) -> list[dict]:
    """
    Por situação: quem detecta melhor, a maior vantagem (p.p.) e em que efeito,
    e o efeito necessário para PODER_ALVO. Usado nos textos do G4 e da conclusão.
    """
    resumos = []
    for condicao, grupo in curvas.groupby("condicao", sort=False):
        com_efeito = grupo.loc[grupo["efeito"] > 0]
        poder = com_efeito.pivot(index="efeito", columns="teste", values="taxa_rejeicao") * 100
        vantagem_t = poder["t pareado"] - poder["Wilcoxon pareado"]  # p.p.
        efeito_maior = vantagem_t.abs().idxmax()
        gap = float(vantagem_t[efeito_maior])
        if abs(gap) < EMPATE_PP:
            lider = None
        else:
            lider = "t pareado" if gap > 0 else "Wilcoxon pareado"
        resumos.append({
            "condicao": condicao,
            "n": int(grupo["n"].iloc[0]),
            "lider": lider,
            "outro": next((t for t in TESTES if t != lider), None) if lider else None,
            "vantagem_pp": abs(gap),
            "efeito": float(efeito_maior),
            "poder": {t: float(poder.loc[efeito_maior, t]) for t in TESTES},
            "efeito_80": {
                t: efeito_para_poder(grupo.loc[grupo["teste"] == t], PODER_ALVO) for t in TESTES
            },
        })
    return resumos


def _efeito_80_formatado(efeito: float | None) -> str:
    return f"{efeito:.1%}" if efeito is not None else "nenhum efeito testado"


def _comparacao(resumo: dict, com_nome: bool) -> str:
    """'outliers, 97% × 40% com 8% de efeito' (vencedor × outro), no efeito de maior vantagem."""
    lider, outro = resumo["lider"], resumo["outro"]
    poderes = (f"{resumo['poder'][lider]:.0f}% × {resumo['poder'][outro]:.0f}% "
               f"com {resumo['efeito']:.0%} de efeito")
    return f"{resumo['condicao']}, {poderes}" if com_nome else poderes


def _leitura_g4(curvas: pd.DataFrame) -> str:
    """
    Texto do G4 em até 3 frases (a 4ª é a introdução da seção): a base e,
    agrupadas pelo teste que vence, as situações com violação.
    """
    base, *violacoes = resumo_poder(curvas)
    e80 = base["efeito_80"]
    if base["lider"] is None:
        comparacao_base = "os dois praticamente empatam"
    else:
        comparacao_base = (f"o **{base['lider']}** detecta melhor, com até "
                           f"{base['vantagem_pp']:.0f} p.p. a mais")
    frases = [
        f"Na **{base['condicao']}** (n={base['n']}), {comparacao_base}: para "
        f"{PODER_ALVO:.0%} de poder, o t precisa de {_efeito_80_formatado(e80['t pareado'])} "
        f"de efeito e o Wilcoxon de {_efeito_80_formatado(e80['Wilcoxon pareado'])}."
    ]

    for lider in ("Wilcoxon pareado", "t pareado"):
        grupo = [r for r in violacoes if r["lider"] == lider]
        if not grupo:
            continue
        mudou = "a vantagem muda de lado e " if lider != base["lider"] else ""
        frases.append(
            f"Com **{' e '.join(r['condicao'] for r in grupo)}**, {mudou}o **{lider}** detecta "
            f"melhor ({'; '.join(_comparacao(r, com_nome=len(grupo) > 1) for r in grupo)})."
        )
    empates = [r["condicao"] for r in violacoes if r["lider"] is None]
    if empates:
        frases.append(f"Com **{' e '.join(empates)}**, os dois praticamente empatam.")
    return " ".join(frases)


def secao_poder() -> None:
    st.header("5. Poder")
    q2, q3 = DATA / "q2.csv", DATA / "q3.csv"
    if not (q2.exists() and q3.exists()):
        st.warning("Rode `python simular_q2.py` e `python simular_q3.py` para gerar o G4.")
        return

    curvas = curvas_poder(pd.read_csv(q2), pd.read_csv(q3))
    st.pyplot(fig_g4(curvas, PODER_ALVO))
    st.markdown(
        "Cada ponto é a proporção de rejeições de H₀ em 10.000 conjuntos com o cache "
        "reduzindo o tempo de build pelo efeito do eixo x (em efeito 0, é o erro tipo I "
        "do G3): quanto mais cedo a curva sobe, mais poder o teste tem. "
        + _leitura_g4(curvas)
    )


COHEN_GRANDE = 0.8  # d a partir do qual Cohen chama o efeito de grande


def _efeito_formatado(teste: dict) -> str:
    """Tamanho de efeito de cada teste na própria escala e em segundos."""
    efeito = teste["tamanho_efeito"]
    if teste["teste"] == "t pareado":
        inferior, superior = efeito["ic95_diferenca_media_s"]
        return (
            f"d_z = {efeito['d_z']:.2f}; diferença média {efeito['diferenca_media_s']:.3f} s "
            f"(IC 95%: {inferior:.3f} a {superior:.3f} s), "
            f"redução de {efeito['reducao_relativa_media']:.0%}"
        )
    return (
        f"r = {efeito['r_rank_biserial']:.2f}; diferença mediana "
        f"{efeito['diferenca_mediana_s']:.3f} s (Hodges-Lehmann {efeito['hodges_lehmann_s']:.3f} s), "
        f"redução de {efeito['reducao_relativa_mediana']:.0%}"
    )


def _conclusao_teste(teste: dict, alpha: float) -> str:
    if not teste["rejeita_h0"]:
        return f"Não rejeita H₀ (p ≥ {alpha}): sem evidência de que o cache muda o tempo"
    efeito = teste["tamanho_efeito"]
    # D = sem − com: positivo quer dizer build mais rápido com cache
    centro = (efeito["diferenca_media_s"] if teste["teste"] == "t pareado"
              else efeito["diferenca_mediana_s"])
    sentido = "reduz" if centro > 0 else "aumenta"
    return f"Rejeita H₀ (p < {alpha}): o cache {sentido} o tempo de build"


def _leitura_dados_reais(res: dict, curvas: pd.DataFrame | None) -> str:
    """Texto da seção 6 montado a partir do JSON e das curvas de poder."""
    t, w = (next(x for x in res["testes"] if x["teste"] == nome)
            for nome in ("t pareado", "Wilcoxon pareado"))
    et, ew = t["tamanho_efeito"], w["tamanho_efeito"]

    aplicacao = (f"Aplicados aos {res['n_pares']} pares de `data/builds.csv` "
                 f"(bicaudais, α = {res['alpha']}), ")
    if t["rejeita_h0"] == w["rejeita_h0"]:
        decisao = "rejeitam" if t["rejeita_h0"] else "não rejeitam"
        frase = aplicacao + f"os dois testes {decisao} H₀ e chegam à mesma conclusão. "
    else:
        frase = (aplicacao + "os testes discordam: só o "
                 f"{t['teste'] if t['rejeita_h0'] else w['teste']} rejeita H₀. ")

    tamanho = "grande" if abs(et["d_z"]) >= COHEN_GRANDE else "menor que o limiar de efeito grande"
    frase += (f"Estatisticamente o efeito é {tamanho}: d_z = {et['d_z']:.2f} "
              f"(Cohen chama de grande a partir de {COHEN_GRANDE}) e r = {ew['r_rank_biserial']:.2f}")
    if ew["r_rank_biserial"] == 1:
        frase += ", ou seja, todos os pares ficaram mais rápidos com cache"
    tempo_sem_cache = et["diferenca_media_s"] / et["reducao_relativa_media"]
    frase += (
        f". Na prática, são {et['diferenca_media_s']:.3f} s a menos por build "
        f"(redução de {et['reducao_relativa_media']:.0%}): a importância prática não vem do "
        f"p-valor, e sim de quanto esse tempo pesa; num build de {tempo_sem_cache:.2f} s "
        "quase não se sente, num build de minutos uma redução dessas mudaria o dia a dia do time."
    )

    if curvas is not None:
        base = curvas.loc[curvas["condicao"] == curvas["condicao"].iloc[0]]
        maior = base["efeito"].max()
        poder = base.loc[base["efeito"] == maior, "taxa_rejeicao"].min()
        if et["reducao_relativa_media"] > maior:
            frase += (
                f" O efeito real (~{et['reducao_relativa_media']:.0%}) passa muito do maior "
                f"efeito do G4 na situação base ({maior:.0%}), onde os dois já têm "
                f"{poder:.0%} de poder; por isso a concordância aqui não mostra qual teste é "
                "melhor, e essa resposta vem das simulações."
            )
    return frase


def secao_dados_reais() -> None:
    st.header("6. Dados reais")
    path = DATA / "testes_reais.json"
    if not path.exists():
        st.warning(
            "Rode `python testar_simulado.py --input data/builds.csv "
            "--output data/testes_reais.json` para gerar o resultado."
        )
        return

    res = json.loads(path.read_text(encoding="utf-8"))
    alpha = res["alpha"]
    st.table(
        pd.DataFrame(
            {
                "Teste": t["teste"],
                "Estatística": f"{t['nome_estatistica']} = {t['estatistica']:.4g}",
                "p-valor": f"{t['p_valor']:.3g}",
                "Tamanho do efeito": _efeito_formatado(t),
                "Conclusão": _conclusao_teste(t, alpha),
            }
            for t in res["testes"]
        ).set_index("Teste")
    )

    q2, q3 = DATA / "q2.csv", DATA / "q3.csv"
    curvas = curvas_poder(pd.read_csv(q2), pd.read_csv(q3)) if q2.exists() and q3.exists() else None
    st.markdown(_leitura_dados_reais(res, curvas))


LIMITACOES = (
    "O estudo tem limites que vale deixar claros. Medimos um projeto de demonstração feito para o "
    "trabalho, numa única máquina, então tanto o efeito do cache quanto a variação entre builds "
    "dependem desse ambiente. A lognormal acompanha bem o centro dos dados, mas não gera sozinha "
    "os builds lentos: eles só entram na situação com outliers, que é um modelo simples (um build "
    "3× mais lento em 5% dos pares). Na simulação, os dois lados do par usam a variação do build "
    "sem cache, e nos dados reais os builds com cache variam mais. Também só testamos α = 0.05 e "
    "amostras de 30 e de 8 pares."
)


def _taxa(taxas: pd.DataFrame, condicao: str, teste: str) -> float:
    linha = taxas.loc[(taxas["condicao"] == condicao) & (taxas["teste"] == teste)]
    return float(linha["taxa_rejeicao"].iloc[0])


def _esperado_encontrado(taxas: pd.DataFrame, resumos: list[dict], reais: dict) -> list[tuple[str, str]]:
    """Linhas da tabela 'esperávamos × encontramos'; a expectativa é a de docs/cenario.md."""
    base, *violacoes = resumos
    nome_base = base["condicao"]
    ganha_w = [r for r in violacoes if r["lider"] == "Wilcoxon pareado"]
    ganha_t = [r for r in violacoes if r["lider"] == "t pareado"]
    p_t, p_w = (next(t["p_valor"] for t in reais["testes"] if t["teste"] == nome) for nome in TESTES)

    linhas = [(
        "Que os dois testes errassem perto de 5% quando o cache não muda nada.",
        f"Foi o que aconteceu com os dados sem problemas: {_taxa(taxas, nome_base, 't pareado'):.1%} "
        f"no t e {_taxa(taxas, nome_base, 'Wilcoxon pareado'):.1%} no Wilcoxon.",
    )]
    if ganha_w:
        erros_t = " e ".join(f"{_taxa(taxas, r['condicao'], 't pareado'):.1%}" for r in ganha_w)
        linhas.append((
            "Que o Wilcoxon se saísse melhor com dados assimétricos ou com outliers.",
            f"Com outliers, sim, e com folga: ele chegou a detectar "
            f"{max(r['vantagem_pp'] for r in ganha_w):.0f} pontos percentuais a mais que o t, que "
            f"ficou conservador ({erros_t} de erro tipo I).",
        ))
    if ganha_t:
        erros_w = " e ".join(f"{_taxa(taxas, r['condicao'], 'Wilcoxon pareado'):.1%}" for r in ganha_t)
        linhas.append((
            "Que essa vantagem do Wilcoxon aparecesse em todas as situações difíceis.",
            f"Não apareceu com poucos dados: com só {ganha_t[0]['n']} pares e sem outliers, o t "
            f"detectou até {max(r['vantagem_pp'] for r in ganha_t):.0f} pontos a mais, e o Wilcoxon "
            f"ficou em {erros_w} de erro tipo I, porque com tão poucos pares ele tem poucos "
            "resultados possíveis.",
        ))
    linhas.append((
        "Que os dois percebessem o efeito do cache nos nossos builds.",
        f"Perceberam, e com muita margem: p = {p_t:.2g} no t e {p_w:.2g} no Wilcoxon.",
    ))
    return linhas


def secao_conclusao(reais: pd.DataFrame) -> None:
    st.header("7. Conclusão")
    arquivos = [DATA / nome for nome in ("q1.csv", "q2.csv", "q3.csv", "testes_reais.json")]
    if not all(caminho.exists() for caminho in arquivos):
        st.warning(
            "Rode `python simular_q1.py`, `simular_q2.py`, `simular_q3.py` e "
            "`testar_simulado.py --input data/builds.csv --output data/testes_reais.json`."
        )
        return

    q1, q2, q3 = (pd.read_csv(caminho) for caminho in arquivos[:3])
    taxas = taxas_erro_tipo_i(q1, q3)
    resumos = resumo_poder(curvas_poder(q2, q3))
    res_reais = json.loads(arquivos[3].read_text(encoding="utf-8"))

    st.markdown("Antes de rodar as simulações, anotamos o que esperávamos (está em `docs/cenario.md`). "
                "Comparando com o que vimos:")
    st.table(pd.DataFrame(
        _esperado_encontrado(taxas, resumos, res_reais),
        columns=["O que esperávamos", "O que vimos"],
    ).set_index("O que esperávamos"))

    base, *violacoes = resumos
    ganha_w = [r for r in violacoes if r["lider"] == "Wilcoxon pareado"]
    ganha_t = [r for r in violacoes if r["lider"] == "t pareado"]
    perda_base = base["vantagem_pp"] if base["lider"] == "t pareado" else 0.0
    com_cache = reais.loc[reais["condicao"] == "com_cache"]
    n_outliers = len(outliers_iqr(com_cache)["builds"])

    paragrafos = [
        "No fim, ficamos com o **Wilcoxon pareado** para comparar tempo de build com e sem cache. "
        f"O que pesou foram os builds lentos isolados: na nossa própria coleta, {n_outliers} dos "
        f"{len(com_cache)} builds com cache ficaram bem acima dos outros."
    ]
    if ganha_w:
        paragrafos[0] += (
            f" Quando simulamos situações assim, o t perdeu até "
            f"{max(r['vantagem_pp'] for r in ganha_w):.0f} pontos de poder, enquanto, com os dados "
            f"sem outliers, o Wilcoxon ficou no máximo {perda_base:.0f} pontos atrás. Abrimos mão de "
            "muito pouco para nos proteger de um problema que vimos acontecer."
        )
    if ganha_t:
        paragrafos.append(
            "Mudaríamos de ideia se tivéssemos pouquíssimas medições e nenhum build fora da curva: "
            f"com {ganha_t[0]['n']} pares, o Wilcoxon não consegue usar todo o α e o t passou na "
            "frente. O t também faz mais sentido quando a pergunta é quanto tempo o cache economiza "
            "em média, porque ele já entrega essa diferença em segundos, com intervalo de confiança."
        )
    paragrafos.append(LIMITACOES)
    st.markdown("\n\n".join(paragrafos))


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
    secao_poder()
    secao_dados_reais()
    secao_conclusao(reais)
