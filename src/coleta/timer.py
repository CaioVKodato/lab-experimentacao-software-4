from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class TimedResult:
    elapsed_s: float
    returncode: int
    stdout: str
    stderr: str


def run_timed(cmd: list[str], *, cwd: str | None = None) -> TimedResult:
    """Executa um comando e devolve o tempo de parede em segundos."""
    started = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    return TimedResult(
        elapsed_s=elapsed,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
