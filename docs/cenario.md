# Cenário — Lab 04 (P2)

## Pergunta

O cache reduz o tempo de build do projeto demo?

## Hipóteses

- **H₀:** a mediana (ou média, no t pareado) da diferença de tempo sem cache − com cache é zero; ativar o cache não muda o tempo de build.
- **H₁:** a diferença é diferente de zero (bicaudal); o cache altera o tempo de build.

Testes: **t pareado** × **Wilcoxon pareado**.

## Dados reais

Fonte: `data/builds.csv`, gerado por `python coletar_builds.py` no fixture `fixtures/demo_build/`.

- 15 pares (`sem_cache` / `com_cache`)
- Unidade: segundos

Resumo (via `python estimar_params.py` → `data/params.json`):

| Condição   | n  | Mediana | Média  | Desvio | Assimetria |
|------------|----|---------|--------|--------|------------|
| sem_cache  | 15 | 0.268 s | 0.270 s | 0.010 | 1.14 |
| com_cache  | 15 | 0.110 s | 0.123 s | 0.028 | 1.85 |

Diferença pareada (sem − com): mediana ≈ **0.154 s**, média ≈ **0.147 s**.  
Efeito relativo mediano ≈ **57%** do tempo sem cache.

Os tempos são positivos e assimétricos (skew > 1 nos dois grupos), com mais dispersão quando o cache está ligado.

## Como a simulação será gerada

Distribuição: **lognormal** em cada condição, com `mu` e `sigma` estimados em `log(tempo_s)`:

- sem_cache: μ ≈ -1.310, σ ≈ 0.037  
- com_cache: μ ≈ -2.119, σ ≈ 0.197  
- n por grupo na simulação base: 15 (igual à amostra real)

Parâmetros versionados em `data/params.json`.

## Expectativa antes de simular

Esperamos que o **Wilcoxon pareado** se saia melhor (ou pelo menos tão bem) que o t pareado quando os dados forem bem assimétricos ou tiverem outliers — que é o caso do `com_cache` (skew ≈ 1.85).

Com H₀ verdadeira e dados “bem comportados”, os dois devem ficar perto de 5% de erro tipo I.  
No poder, se a diferença for grande como na amostra real (~0.15 s), os dois devem detectar o efeito com n=15; a vantagem do Wilcoxon deve aparecer mais nas violações (Q3).
