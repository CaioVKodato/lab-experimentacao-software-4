from __future__ import annotations

from .config import CollectConfig
from .csv_writer import write_builds_csv
from .timer import run_timed


def _ensure_ok(label: str, returncode: int, stderr: str) -> None:
    if returncode == 0:
        return
    detail = stderr.strip() or "(sem stderr)"
    raise RuntimeError(f"{label} falhou (code={returncode}): {detail}")


def collect_build_times(config: CollectConfig | None = None) -> list[dict]:
    """
    Para cada par i=1..n:
      1. limpa o cache
      2. build sem cache (frio)
      3. build com cache (quente, reaproveitando o que o passo 2 gravou)

    Retorna as linhas que vão para o CSV (duas por par).
    """
    cfg = config or CollectConfig()
    if not cfg.build_script.exists():
        raise FileNotFoundError(f"build script não encontrado: {cfg.build_script}")

    cwd = str(cfg.project_dir)
    rows: list[dict] = []

    for run_id in range(1, cfg.n_pairs + 1):
        cleared = run_timed(cfg.clear_cache_cmd(), cwd=cwd)
        _ensure_ok(f"clear-cache run={run_id}", cleared.returncode, cleared.stderr)

        cold = run_timed(cfg.build_sem_cache_cmd(), cwd=cwd)
        _ensure_ok(f"build sem_cache run={run_id}", cold.returncode, cold.stderr)

        # popula o cache uma vez antes da medição "com cache"
        warm_up = run_timed(cfg.build_com_cache_cmd(), cwd=cwd)
        _ensure_ok(f"warmup com_cache run={run_id}", warm_up.returncode, warm_up.stderr)

        warm = run_timed(cfg.build_com_cache_cmd(), cwd=cwd)
        _ensure_ok(f"build com_cache run={run_id}", warm.returncode, warm.stderr)

        rows.append(
            {"run": run_id, "condicao": "sem_cache", "tempo_s": cold.elapsed_s}
        )
        rows.append(
            {"run": run_id, "condicao": "com_cache", "tempo_s": warm.elapsed_s}
        )
        print(
            f"run={run_id:02d}  sem_cache={cold.elapsed_s:.4f}s  "
            f"com_cache={warm.elapsed_s:.4f}s"
        )

    write_builds_csv(cfg.output_csv, rows)
    return rows
