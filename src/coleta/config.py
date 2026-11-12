from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_BUILD = REPO_ROOT / "fixtures" / "demo_build"
DEFAULT_CSV = REPO_ROOT / "data" / "builds.csv"
# o enunciado pede cerca de 30 observações por grupo comparado
DEFAULT_N_PAIRS = 30


@dataclass(frozen=True)
class CollectConfig:
    """Parâmetros da coleta de tempos de build."""

    project_dir: Path = DEMO_BUILD
    output_csv: Path = DEFAULT_CSV
    n_pairs: int = DEFAULT_N_PAIRS
    python_exe: str = "python"

    @property
    def build_script(self) -> Path:
        return self.project_dir / "build.py"

    def clear_cache_cmd(self) -> list[str]:
        return [self.python_exe, str(self.build_script), "--clear-cache"]

    def build_sem_cache_cmd(self) -> list[str]:
        return [self.python_exe, str(self.build_script), "--no-cache"]

    def build_com_cache_cmd(self) -> list[str]:
        return [self.python_exe, str(self.build_script)]
