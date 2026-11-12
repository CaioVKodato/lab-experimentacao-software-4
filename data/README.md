# Dados de build

## Origem

| Item | Valor |
|---|---|
| Fonte | Projeto demo em `fixtures/demo_build/` deste repositório |
| Link | https://github.com/CaioVKodato/lab-experimentacao-software-4/tree/main/fixtures/demo_build |
| Arquivo | `data/builds.csv` |
| Quantidade | 30 pares, 60 builds (30 sem cache + 30 com cache) |
| Coleta | 11/11/2026, uma rodada de `python coletar_builds.py` (29 s no total) |
| Máquina | Windows 11 Home, Intel Core i5-1135G7 2,40 GHz, Python 3.12.10 |

O demo é um build em Python que processa os módulos de `src/` e grava artefatos em `.cache/`. Ele serve para medir o efeito do cache de forma repetível na máquina local, sem depender de um repositório externo.

## Como a coleta funciona

Comando:

```bash
python coletar_builds.py
```

Para cada par (30 por padrão, `DEFAULT_N_PAIRS` em `src/coleta/config.py`; mude com `--n-pairs`):

1. limpa o `.cache/`
2. roda o build **sem cache** (`--no-cache`) e mede o tempo
3. popula o cache (warmup, não entra no CSV)
4. roda o build **com cache** e mede o tempo

Os dois builds de um par rodam em sequência, então pegam o mesmo estado da máquina. É isso que justifica o teste **pareado**.

## Variáveis

| Coluna | Tipo | Significado |
|---|---|---|
| `run` | inteiro, 1–30 | número do par; liga o build sem cache ao com cache |
| `condicao` | `sem_cache` / `com_cache` | cache desligado / ligado (após warmup) |
| `tempo_s` | real, segundos | tempo de parede do build, medido com `time.perf_counter` |

## Distribuição

Resumo gerado por `python estimar_params.py` (`data/params.json`):

| Condição | Mediana | Média | Desvio | Mín–máx | Assimetria |
|---|---|---|---|---|---|
| sem_cache | 0,311 s | 0,317 s | 0,022 s | 0,293–0,369 s | 0,95 |
| com_cache | 0,155 s | 0,166 s | 0,036 s | 0,135–0,306 s | 2,33 |
| diferença (sem − com) | 0,157 s | 0,151 s | 0,035 s | 0,054–0,214 s | −1,08 |

- Tempos positivos e **assimétricos à direita** nas duas condições, bem mais com cache.
- **Outliers** (regra de 1,5·IQR, `outliers_iqr` em `data/params.json`): nenhum sem cache; com cache, os runs **10 (0,306 s)** e **21 (0,239 s)**, acima do limite de 0,233 s. No run 10 o build sem cache também foi o mais lento da coleta (0,369 s), o que sugere a máquina ocupada naquele momento. Os dois ficaram no CSV: são medições reais e nenhum dado foi removido.
- O cache reduziu o tempo nos 30 pares (todas as diferenças são positivas).

## Observações

- Os tempos dependem da máquina e da carga do momento: numa coleta anterior de 15 pares, a mediana sem cache foi 0,268 s.
- O cache fica só em `fixtures/demo_build/.cache/` e não vai para o git.
