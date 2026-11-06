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

Gera `data/builds.csv` (~15 pares com/sem cache).

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

Dashboard (S01/S02): *(preencher — comando único)*

## Sprint 1 (Issues)

| # | Issue | Assignee |
|---|-------|----------|
| 1 | Script de coleta dos tempos de build | CaioVKodato |
| 2 | Estimativa de parâmetros | CaioVKodato |
| 3 | Gerador de dados simulados | Henrique-volponi |
| 4 | t pareado e Wilcoxon | Henrique-volponi |
| 5 | Dashboard base + G1 | Kjonps |
| 6 | G2 no dashboard | Kjonps |
