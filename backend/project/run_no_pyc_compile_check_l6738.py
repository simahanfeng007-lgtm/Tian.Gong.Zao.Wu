from __future__ import annotations

"""L6.73.8 syntax compilation helper that never writes __pycache__ / *.pyc."""

import argparse
import json
import sys
import tokenize
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


def _iter_py(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".py" else []
    return sorted(p for p in target.rglob("*.py") if "__pycache__" not in p.parts)


def _public(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except Exception:
        return path.name


def compile_no_pyc(targets: list[Path]) -> dict[str, Any]:
    files: list[Path] = []
    for target in targets:
        files.extend(_iter_py(target))
    errors: list[dict[str, str]] = []
    for path in files:
        try:
            with tokenize.open(str(path)) as handle:
                source = handle.read()
            compile(source, _public(path), "exec", dont_inherit=True)
        except Exception as exc:
            errors.append({"file": _public(path), "error": f"{exc.__class__.__name__}: {exc}"})
    return {"ok": not errors, "files_checked": len(files), "errors": errors[:30]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="L6.73.8 no-pyc syntax compile check")
    parser.add_argument("targets", nargs="*")
    args = parser.parse_args(argv)
    package_root = Path(__file__).resolve().parents[2]
    if args.targets:
        targets = [Path(item) for item in args.targets]
    else:
        targets = [
            package_root / "backend" / "project",
            package_root / "desktop",
            package_root / "frontend" / "linyuanzhe_frontend",
            package_root / "scripts",
        ]
    result = compile_no_pyc(targets)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
