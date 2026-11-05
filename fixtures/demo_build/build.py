"""
Build demo com cache em disco.

Sem cache (ou cache limpo): processa todos os módulos de src/.
Com cache quente: reutiliza artefatos em .cache/ e só reprocessa o que mudou.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
CACHE_DIR = ROOT / ".cache"
MANIFEST = CACHE_DIR / "manifest.json"


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict[str, str]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _run_module(path: Path) -> int:
    """Carrega o .py e chama work(), simulando compilação/processamento."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # custo extra proposital: o cache evita repetir isso
    time.sleep(0.05)
    return int(module.work())


def _artifact_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.out"


def build(*, use_cache: bool) -> dict:
    started = time.perf_counter()
    modules = sorted(SRC_DIR.glob("*.py"))
    if not modules:
        raise FileNotFoundError(f"nenhum módulo em {SRC_DIR}")

    manifest = _load_manifest() if use_cache else {}
    results: dict[str, int] = {}
    processed = 0
    cached = 0

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for path in modules:
        digest = _file_digest(path)
        artifact = _artifact_path(path.stem)
        hit = (
            use_cache
            and manifest.get(path.name) == digest
            and artifact.exists()
        )

        if hit:
            results[path.stem] = int(artifact.read_text(encoding="utf-8"))
            cached += 1
            continue

        value = _run_module(path)
        results[path.stem] = value
        processed += 1
        if use_cache:
            artifact.write_text(str(value), encoding="utf-8")
            manifest[path.name] = digest

    if use_cache:
        _save_manifest(manifest)

    elapsed = time.perf_counter() - started
    return {
        "elapsed_s": elapsed,
        "processed": processed,
        "cached": cached,
        "results": results,
    }


def clear_cache() -> None:
    if not CACHE_DIR.exists():
        return
    for path in CACHE_DIR.iterdir():
        if path.is_file():
            path.unlink()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    use_cache = "--no-cache" not in args

    if "--clear-cache" in args:
        clear_cache()
        print("cache limpo")
        return 0

    summary = build(use_cache=use_cache)
    mode = "com_cache" if use_cache else "sem_cache"
    print(
        f"mode={mode} elapsed_s={summary['elapsed_s']:.4f} "
        f"processed={summary['processed']} cached={summary['cached']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
