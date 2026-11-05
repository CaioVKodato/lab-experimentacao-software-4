"""Entry point: python estimar_params.py"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from params.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
