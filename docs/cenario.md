# Cenário — Lab 04 (P2)

## Pergunta

Ativar o cache muda o tempo de build do projeto demo?

## Hipóteses

Em cada par *i*, o mesmo build é medido sem e com cache. A variável analisada é a diferença

D_i = T_sem,i − T_com,i   (segundos; positiva quando o cache deixa o build mais rápido)

| Teste | H₀ (notação) | H₀ (em palavras) | H₁ (notação) | H₁ (em palavras) |
|---|---|---|---|---|
| t pareado | μ_D = 0 | em média, ligar o cache não muda o tempo de build | μ_D ≠ 0 | em média, o tempo muda (para menos ou para mais) |
| Wilcoxon pareado | D simétrica em torno de 0 (mediana = 0) | ganhar ou perder tempo com o cache é igualmente provável | D deslocada de 0 (mediana ≠ 0) | o cache tende a acelerar ou a atrasar o build |

Testes: **t pareado** × **Wilcoxon pareado**, com α = 0,05.

### Por que bicaudal

A pergunta é se o cache **muda** o tempo, não só se reduz. Antes de medir, não dava para descartar que o cache deixasse o build mais lento: com ele ligado, o build lê e grava artefatos e o manifesto em disco, um custo que pode superar a economia em projetos pequenos. O bicaudal divide α em 2,5% para cada cauda e detecta efeito nos dois sentidos. Também é a escolha mais conservadora: o valor crítico do t com 29 gl é 2,05, contra 1,70 no unicaudal. Se H₀ for rejeitada, o sinal de D diz para que lado o cache mexeu.

Escolher unicaudal depois de olhar os dados (porque o cache "claramente" reduziu) dobraria o erro tipo I na prática, então a decisão foi fixada antes da coleta.

## Dados reais

Fonte: `data/builds.csv`, gerado por `python coletar_builds.py` no fixture `fixtures/demo_build/`.

- 30 pares (`sem_cache` / `com_cache`)
- Unidade: segundos

Resumo (via `python estimar_params.py` → `data/params.json`):

| Condição   | n  | Mediana | Média  | Desvio | Assimetria |
|------------|----|---------|--------|--------|------------|
| sem_cache  | 30 | 0.311 s | 0.317 s | 0.022 | 0.95 |
| com_cache  | 30 | 0.155 s | 0.166 s | 0.036 | 2.33 |

Diferença pareada (sem − com): mediana ≈ **0.157 s**, média ≈ **0.151 s**.  
Efeito relativo mediano ≈ **51%** do tempo sem cache.

Os tempos são positivos e assimétricos à direita (assimetria 0.95 sem cache e 2.33 com cache), com mais dispersão quando o cache está ligado.

Outliers pela regra de 1,5·IQR (gravados em `data/params.json`, `outliers_iqr`): nenhum sem cache; 2 com cache, os runs 10 (0.306 s) e 21 (0.239 s), acima do limite de 0.233 s. São eles que puxam a assimetria do `com_cache` para 2.33, e são a base real da violação por outliers do Q3. Registro completo da coleta em `data/README.md`.

## Como a simulação será gerada

Distribuição: **lognormal** em cada condição, com `mu` e `sigma` estimados em `log(tempo_s)`:

- sem_cache: μ ≈ -1.150, σ ≈ 0.068  
- com_cache: μ ≈ -1.812, σ ≈ 0.186  
- n por grupo na simulação base: 30 (igual à amostra real)

Parâmetros versionados em `data/params.json`.

### Grade de efeitos do Q2 (poder)

Nas simulações de erro tipo I e poder, os dois tempos do par saem da **mesma** lognormal (a do build sem cache, μ ≈ -1.150, σ ≈ 0.068), então a diferença é simétrica em torno de zero e H₀ vale para os dois testes. O efeito entra como **redução relativa** do tempo com cache: `com = com × (1 − efeito)`.

Grade: **0%, 1%, 2%, 3%, 4%, 5%, 6%, 8% e 10%**, com 10.000 repetições cada e n = 30 pares (`python simular_q2.py` → `data/q2.csv`).

Por que esses valores e não o efeito real: na amostra coletada o cache reduz o tempo em ~50%, o que dá poder de 100% nos dois testes já com poucos pares — a curva seria uma linha reta em 1. Com a variação de ~7% entre builds (σ em log), a curva sai de 5% em efeito 0, passa de 80% por volta de 5% e chega a ~100% em 10%. A grade é mais fina até 6% porque é onde o poder muda rápido, e começa em zero para ligar com o Q1.

### Q3: violação dos pressupostos

O pressuposto violado é a **normalidade das diferenças** (sem − com), que o t pareado usa para dizer que a estatística segue uma t com n−1 graus de liberdade. O Wilcoxon pareado só pede que as diferenças sejam simétricas em torno de zero sob H₀.

Situações simuladas (`python simular_q3.py` → `data/q3.csv`, coluna `condicao`; mesma grade do Q2 mais 15% e 20%, 10.000 repetições, semente 42):

- **outliers (n = 30):** em 5% dos pares, um dos dois builds demora 3× mais (lado sorteado 50/50). Imita um build que pegou disco frio ou CPU ocupada.
- **amostra pequena (n = 8):** a base lognormal com poucos pares.
- **amostra pequena + outliers (n = 8):** as duas coisas juntas.

O lado do outlier é sorteado para a diferença continuar simétrica em torno de zero: H₀ é verdadeira para os dois testes e a comparação é justa (uma diferença assimétrica de média zero tornaria H₀ falsa para o Wilcoxon). Também testamos σ maior na lognormal, mas a diferença de dois tempos i.i.d. continua quase normal e nada muda, então essa situação ficou de fora.

**Por que afeta mais o t:** um outlier entra inteiro na média e, ao quadrado, no desvio padrão das diferenças. O desvio cresce mais que a média, o |t| encolhe e o teste quase não rejeita: com outliers, o erro tipo I do t cai para ~1,5% (conservador) e o poder com 5% de efeito despenca de 81% para 23%. O Wilcoxon usa postos, então um outlier vale no máximo o maior posto, e ele fica em ~5% de erro tipo I e 69% de poder.

Com **n = 8** sem outliers a vantagem muda de lado: o Wilcoxon exato só tem 2⁸ = 256 resultados possíveis, então não consegue usar todo o α (erro tipo I ~3,9%) e perde poder para o t (69% × 76% com 10% de efeito). Com n = 8 + outliers, o Wilcoxon volta a ganhar nos efeitos maiores (82% × 67% com 20%).

## Expectativa antes de simular

Esperamos que o **Wilcoxon pareado** se saia melhor (ou pelo menos tão bem) que o t pareado quando os dados forem bem assimétricos ou tiverem outliers — que é o caso do `com_cache` (assimetria ≈ 2.33).

Com H₀ verdadeira e dados “bem comportados”, os dois devem ficar perto de 5% de erro tipo I.  
No poder, se a diferença for grande como na amostra real (~0.15 s), os dois devem detectar o efeito com n=30; a vantagem do Wilcoxon deve aparecer mais nas violações (Q3).
