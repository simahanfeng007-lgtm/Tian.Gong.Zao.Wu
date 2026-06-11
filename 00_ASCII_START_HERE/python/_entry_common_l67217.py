from __future__ import annotations

"""L6.73.8 import-safe entry common layer.

This module is the only Python entry helper used by categorized launchers.
It remains deliberately side-effect light: importing it must not start desktop UI,
run self-check, invoke DataUp, mutate sys.argv, or call runpy.
"""

import os
import runpy
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Iterable, Sequence

VERSION_LABEL = "FE01 STEP68 / L6.73.8"
DEFAULT_DATAUP_TIMEOUT_SECONDS = 600


def looks_like_project_root(candidate: Path) -> bool:
    return (
        (candidate / "desktop" / "start_linyuanzhe_desktop_l671.py").exists()
        and (candidate / "frontend" / "linyuanzhe_frontend" / "app.py").exists()
        and (candidate / "backend" / "project" / "run_agent.py").exists()
        and (candidate / "00_ASCII_START_HERE" / "python" / "START_DESKTOP_L6710.py").exists()
    )


def iter_up(start: Path) -> Iterable[Path]:
    resolved = start.expanduser().resolve()
    yield resolved
    yield from resolved.parents


def _usable_hint(raw: str) -> Path | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        path = Path(value).expanduser()
    except (OSError, ValueError):
        return None
    # Current entry contract: stale or malformed environment hints are ignored first.
    # This prevents an old TIANGONG_ROOT_HINT from biasing root discovery.
    try:
        if not path.exists():
            return None
        if path.is_file():
            return path.parent
        if path.is_dir():
            return path
    except OSError:
        return None
    return None


def _candidate_hints(anchor: Path) -> list[Path]:
    hints: list[Path] = []
    for raw in (
        os.environ.get("LINYUANZHE_ROOT_HINT", ""),
        # Backward compatibility only. New launchers set LINYUANZHE_ROOT_HINT.
        os.environ.get("TIANGONG_ROOT_HINT", ""),
        str(Path.cwd()),
        str(anchor),
    ):
        hint = _usable_hint(raw)
        if hint is not None:
            hints.append(hint)
    return hints


def find_project_root(anchor: Path) -> Path:
    seen: set[Path] = set()
    for path in _candidate_hints(anchor):
        for candidate in iter_up(path):
            if candidate in seen:
                continue
            seen.add(candidate)
            if looks_like_project_root(candidate):
                return candidate
    raise SystemExit(
        "Project root not found. Keep desktop, frontend, backend and "
        "00_ASCII_START_HERE in the same extracted package. Do not run "
        "directly inside a compressed ZIP view."
    )


def prepare_entry_environment(root: Path) -> None:
    os.environ["LINYUANZHE_ROOT_HINT"] = str(root)
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


def _entry_debug_enabled() -> bool:
    return os.environ.get("LINYUANZHE_ENTRY_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _print_friendly_entry_error(exc: BaseException, *, entry: Path) -> None:
    print("", file=sys.stderr)
    print("[临渊者入口] 启动失败，入口已拦截普通异常。", file=sys.stderr)
    print(f"[临渊者入口] 入口文件：{entry}", file=sys.stderr)
    print(f"[临渊者入口] 错误类型：{type(exc).__name__}", file=sys.stderr)
    summary = str(exc).strip() or "无错误摘要"
    print(f"[临渊者入口] 错误摘要：{summary}", file=sys.stderr)
    print("[临渊者入口] 建议先运行 SELF_CHECK / DEPENDENCY_CHECK。", file=sys.stderr)
    if _entry_debug_enabled():
        print("[临渊者入口] 调试堆栈如下：", file=sys.stderr)
        traceback.print_exc()
    else:
        print("[临渊者入口] 如需完整堆栈，请设置 LINYUANZHE_ENTRY_DEBUG=1 后重试。", file=sys.stderr)


def _run_desktop_script(root: Path, argv: Sequence[str], *, self_check: bool = False) -> int:
    desktop = root / "desktop"
    entry = desktop / "start_linyuanzhe_desktop_l671.py"
    if not entry.exists():
        raise SystemExit(f"Desktop entry missing: {entry}")
    prepare_entry_environment(root)
    if str(desktop) not in sys.path:
        sys.path.insert(0, str(desktop))
    effective_argv = list(argv)
    if self_check and "--self-check" not in effective_argv:
        effective_argv.insert(0, "--self-check")
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(entry), *effective_argv]
        runpy.run_path(str(entry), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else (0 if code is None else 1)
    except Exception as exc:  # noqa: BLE001 - entry boundary must convert ordinary failures to user-facing diagnostics.
        _print_friendly_entry_error(exc, entry=entry)
        return 1
    finally:
        sys.argv = old_argv
    return 0


def main_start_desktop(argv: Sequence[str] | None = None, *, anchor: Path | None = None) -> int:
    root = find_project_root(anchor or Path(__file__))
    return _run_desktop_script(root, list(sys.argv[1:] if argv is None else argv), self_check=False)


def main_self_check(argv: Sequence[str] | None = None, *, anchor: Path | None = None) -> int:
    root = find_project_root(anchor or Path(__file__))
    return _run_desktop_script(root, list(sys.argv[1:] if argv is None else argv), self_check=True)


def _dataup_timeout_seconds() -> int:
    raw = os.environ.get("LINYUANZHE_DATAUP_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_DATAUP_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_DATAUP_TIMEOUT_SECONDS
    return min(max(value, 30), 3600)


def main_dataup_safe_update(argv: Sequence[str] | None = None, *, anchor: Path | None = None) -> int:
    root = find_project_root(anchor or Path(__file__))
    helper = root / "desktop" / "dataup_update_helper_l6717.py"
    if not helper.exists():
        raise SystemExit(f"DataUp helper missing: {helper}")
    prepare_entry_environment(root)
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = [sys.executable, "-B", str(helper), "--source", "auto", "--apply", "--yes", *args]
    timeout = _dataup_timeout_seconds()
    try:
        return int(subprocess.run(cmd, cwd=str(root), timeout=timeout).returncode)
    except subprocess.TimeoutExpired:
        print(f"[临渊者入口] DataUp 安全更新超过 {timeout} 秒，已终止等待。", file=sys.stderr)
        print("[临渊者入口] 请检查网络、签名包与磁盘权限后重试。", file=sys.stderr)
        return 124
