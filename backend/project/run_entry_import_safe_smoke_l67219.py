from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path


def import_file(path: Path) -> None:
    module_name = "_l67219_import_safe_" + path.stem.replace("-", "_") + "_" + str(abs(hash(str(path))))
    old_path = list(sys.path)
    try:
        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot create module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old_path


def assert_runpy_not_top_level(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and func.attr.startswith("run"):
                raise AssertionError(f"top-level run call detected in {path}")
        if isinstance(node, ast.Call):
            raise AssertionError(f"top-level call detected in {path}")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    entry_files = [
        root / "00_ASCII_START_HERE" / "python" / "START_DESKTOP_L6710.py",
        root / "00_ASCII_START_HERE" / "python" / "SELF_CHECK_L6710.py",
        root / "00_ASCII_START_HERE" / "python" / "DATAUP_SAFE_UPDATE_L6717.py",
        root / "00_ASCII_START_HERE" / "python" / "DEPENDENCY_CHECK.py",
        root / "00_ASCII_START_HERE" / "python" / "PYTHON_PROBE_L67217.py",
        root / "01_启动入口" / "通用Python" / "START_DESKTOP_L6710.py",
        root / "01_启动入口" / "通用Python" / "SELF_CHECK_L6710.py",
        root / "01_启动入口" / "通用Python" / "DATAUP_SAFE_UPDATE_L6717.py",
    ]
    for path in entry_files:
        import_file(path)
    common = root / "00_ASCII_START_HERE" / "python" / "_entry_common_l67217.py"
    import_file(common)
    # The common layer may define runpy.run_path inside a function, but import must not execute it.
    tree = ast.parse(common.read_text(encoding="utf-8"), filename=str(common))
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            raise AssertionError("entry common contains a top-level call expression")
    print(f"entry_import_safe_smoke PASS: {len(entry_files) + 1} Python entry modules import without launching UI/DataUp/SystemExit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
