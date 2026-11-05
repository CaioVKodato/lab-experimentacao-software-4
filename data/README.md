# Dados de build

## Origem

Projeto demo em `fixtures/demo_build/`.

É um build em Python que processa os módulos de `src/` e grava artefatos em `.cache/`. Serve para medir o efeito de cache de forma repetível na máquina local, sem depender de um repositório externo.

## Como a coleta funciona

Comando:

```bash
python coletar_builds.py
```

Para cada um dos 15 pares:

1. limpa o `.cache/`
2. roda o build **sem cache** (`--no-cache`) e mede o tempo
3. popula o cache (warmup, não entra no CSV)
4. roda o build **com cache** e mede o tempo

Saída: `data/builds.csv` com colunas `run`, `condicao`, `tempo_s`.

- `condicao=sem_cache` → cache desligado
- `condicao=com_cache` → cache ligado (após warmup)

## Observações

- Tempos em segundos (parede), medidos no host que rodou o script.
- O cache fica só em `fixtures/demo_build/.cache/` e não vai pro git.
