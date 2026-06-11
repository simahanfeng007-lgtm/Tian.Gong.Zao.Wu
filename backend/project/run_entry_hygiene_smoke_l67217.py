from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCHEMA = "tiangong.l6738.entry_hygiene_smoke.v1"
CURRENT_VERSION = "L6.73.8"
OLD_ENTRY_VERSION = "L6.72." + "20"


def _load_module(path: Path, name: str):
    before_argv = sys.argv[:]
    before_path = sys.path[:]
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert sys.argv == before_argv, f"import mutated sys.argv: {path}"
    # sys.path may be extended by 01_启动入口 stubs so they can import the common module.
    return module


def _assert_text(path: Path, must: list[str], must_not: list[str]) -> None:
    data = path.read_text(encoding="utf-8", errors="ignore")
    for token in must:
        assert token in data, f"{path} missing {token!r}"
    for token in must_not:
        assert token not in data, f"{path} contains forbidden {token!r}"


def _assert_crlf(path: Path) -> None:
    raw = path.read_bytes()
    assert b"\r\n" in raw, f"{path} missing CRLF"
    assert b"\n" not in raw.replace(b"\r\n", b""), f"{path} has non-CRLF line breaks"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    py_entries = [
        root / "00_ASCII_START_HERE/python/START_DESKTOP_L6710.py",
        root / "00_ASCII_START_HERE/python/SELF_CHECK_L6710.py",
        root / "00_ASCII_START_HERE/python/DATAUP_SAFE_UPDATE_L6717.py",
        root / "01_启动入口/通用Python/START_DESKTOP_L6710.py",
        root / "01_启动入口/通用Python/SELF_CHECK_L6710.py",
        root / "01_启动入口/通用Python/DATAUP_SAFE_UPDATE_L6717.py",
    ]
    common = root / "00_ASCII_START_HERE/python/_entry_common_l67217.py"
    probe = root / "00_ASCII_START_HERE/python/PYTHON_PROBE_L67217.py"
    _load_module(common, "entry_common_l67217_smoke")
    _load_module(probe, "python_probe_l67217_smoke")
    for i, path in enumerate(py_entries):
        _load_module(path, f"entry_stub_{i}")
        _assert_text(path, ["if __name__ == \"__main__\""], ["runpy.run_path", "ROOT = find_project_root", "HELPER ="])

    shell_entries = list((root / "00_ASCII_START_HERE/linux_macos").glob("*.sh"))
    shell_entries += list((root / "01_启动入口/Linux").glob("*.sh"))
    shell_entries += list((root / "01_启动入口/macOS").glob("*.command"))
    for path in shell_entries:
        _assert_text(path, [f"SCRIPT_VERSION=\"{CURRENT_VERSION}\"", "validate_python_bin", "python3.[0-9]*", "shopt -s nullglob"], ["L6.72.5", "L6.72.10", OLD_ENTRY_VERSION, "\"$@\""])

    bat_entries = list((root / "00_ASCII_START_HERE/windows").glob("*.bat"))
    bat_entries += list((root / "01_启动入口/Windows").glob("*.bat"))
    bat_entries += list(root.glob("START_FROM_ANYWHERE_AUTO_L672*.bat"))
    bat_entries += list(root.glob("SELF_CHECK_FROM_ANYWHERE_L672*.bat"))
    for path in bat_entries:
        _assert_crlf(path)
        _assert_text(path, ["title %TITLE%", "PYTHON_PROBE_L67217.py", CURRENT_VERSION], [" -c \"import", "TIANGONG_ROOT_HINT", OLD_ENTRY_VERSION, "%*"])

    all_bats = list(root.rglob("*.bat"))
    for path in all_bats:
        _assert_text(path, [], [" -c \"import", "python -c"])

    print({"schema": SCHEMA, "status": "PASS", "python_entries": len(py_entries), "shell_entries": len(shell_entries), "bat_entries": len(bat_entries), "all_bat_no_inline_python_c": len(all_bats)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
