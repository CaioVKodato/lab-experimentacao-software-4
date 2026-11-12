# lab-experimentacao-software-4

Lab 04 — Testes de hipótese (P2: t pareado × Wilcoxon pareado)

Tempo de build antes e depois de ativar o cache.

## Grupo

- [CaioVKodato](https://github.com/CaioVKodato)
- [Henrique-volponi](https://github.com/Henrique-volponi)
- [Kjonps](https://github.com/Kjonps)

## Links

- Repositório: https://github.com/CaioVKodato/lab-experimentacao-software-4
- GitHub Projects: https://github.com/users/CaioVKodato/projects/9

## Como rodar

Coleta dos tempos de build (Issue #1):

```bash
python coletar_builds.py
```

Gera `data/builds.csv` (30 pares com/sem cache; mude com `--n-pairs`).

Estimativa de parâmetros (Issue #2):

```bash
python estimar_params.py
```

Gera `data/params.json`. Cenário em `docs/cenario.md`.

Dados simulados (Issue #3):

```bash
python simular_dados.py            # semente 42, n do params.json
python simular_dados.py --seed 7 --n 30
```

Gera `data/simulado.csv` (mesmo formato de `builds.csv`), com pares lognormais com os parâmetros de `data/params.json`. Mesma semente → mesmo arquivo. Em código: `simulacao.gerar_pares(sim, n, rng)`.

t pareado × Wilcoxon pareado no exemplo simulado (Issue #4):

```bash
python testar_simulado.py                       # data/simulado.csv
python testar_simulado.py --input data/builds.csv --output data/testes_reais.json
```

Grava `data/testes_simulado.json` com estatística, p-valor e interpretação de cada teste (bicaudal, α = 0,05). Em código: `testes.aplicar_testes(sem, com)`.

Q1 — erro tipo I (Issue #13):

```bash
python simular_q1.py
```

Gera `data/q1.csv`: 10.000 conjuntos com H₀ verdadeira (n = 30, sem e com cache da mesma lognormal), taxa de rejeição de cada teste com IC 95% (Wilson, ~±0,43 p.p.). Semente 42 → mesmo arquivo. O motor fica em `src/simulacao/motor.py`: `simular_cenario(Cenario(nome, n, efeito, tipo), sim)` serve também para Q2 (efeito > 0) e Q3 (novos tipos em `GERADORES`).

Q2 — poder com efeitos crescentes (Issue #14):

```bash
python simular_q2.py
python simular_q2.py --efeitos 0 0.02 0.05   # outra grade
```

Gera `data/q2.csv`: taxa de rejeição de cada teste para efeitos de 0% a 10% de redução do tempo com cache (10.000 repetições por efeito, n = 30, semente 42). A escolha da grade está em `docs/cenario.md`.

Dashboard (S01/S02):

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

Abre em http://localhost:8501. Lê `data/builds.csv`, `data/simulado.csv`, `data/params.json` e `data/testes_simulado.json`; os gráficos são gerados em código (`src/painel/graficos.py`).

## Sprint 1 (Issues)

| # | Issue | Assignee |
|---|-------|----------|
| 1 | Script de coleta dos tempos de build | CaioVKodato |
| 2 | Estimativa de parâmetros | CaioVKodato |
| 3 | Gerador de dados simulados | Henrique-volponi |
| 4 | t pareado e Wilcoxon | Henrique-volponi |
| 5 | Dashboard base + G1 | Kjonps |
| 6 | G2 no dashboard | Kjonps |
