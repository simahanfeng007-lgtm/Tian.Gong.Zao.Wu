from __future__ import annotations

"""Windows double-click safe launcher for FE01 STEP68 / L6.73.8.

This wrapper keeps the BAT layer deliberately small.  It owns root discovery,
diagnostic logging, isolated Python child execution (-S -B -u), and friendly
failure output for Windows double-click users.
"""

import argparse
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

VERSION_LABEL = "FE01 STEP68 / L6.73.8"
MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 14)


def _safe_path(raw: str | None) -> Path | None:
    value = (raw or "").strip().strip('"').strip("'")
    if not value:
        return None
    try:
        return Path(value).expanduser()
    except Exception:
        return None


def _iter_up(path: Path) -> Iterable[Path]:
    try:
        start = path.resolve()
    except Exception:
        start = path.absolute()
    if start.is_file():
        start = start.parent
    yield start
    yield from start.parents


def _looks_like_root(path: Path) -> bool:
    return (
        (path / "desktop" / "start_linyuanzhe_desktop_l671.py").exists()
        and (path / "frontend" / "linyuanzhe_frontend" / "app.py").exists()
        and (path / "backend" / "project" / "run_agent.py").exists()
        and (path / "00_ASCII_START_HERE" / "python" / "START_DESKTOP_L6710.py").exists()
    )


def _candidate_paths(anchor: Path, launcher_dir: str, start_dir: str) -> list[Path]:
    out: list[Path] = []
    for raw in (
        os.environ.get("LINYUANZHE_ROOT_HINT"),
        os.environ.get("TIANGONG_ROOT_HINT"),
        launcher_dir,
        start_dir,
        str(Path.cwd()),
        str(anchor),
    ):
        p = _safe_path(raw)
        if p is not None:
            out.append(p)
    home = Path.home()
    for rel in ("Desktop", "Downloads", "Documents", "桌面", "下载", "文档"):
        out.append(home / rel)
    return out


def find_project_root(anchor: Path, *, launcher_dir: str = "", start_dir: str = "") -> Path:
    seen: set[str] = set()
    for path in _candidate_paths(anchor, launcher_dir, start_dir):
        for candidate in _iter_up(path):
            key = str(candidate).casefold()
            if key in seen:
                continue
            seen.add(key)
            if _looks_like_root(candidate):
                return candidate
            # Common case for copied "from anywhere" BAT: search one level down.
            try:
                if candidate.exists() and candidate.is_dir():
                    for child in candidate.iterdir():
                        if child.is_dir() and _looks_like_root(child):
                            return child.resolve()
            except Exception:
                pass
    raise RuntimeError(
        "Project root not found. Fully extract the ZIP first, then keep "
        "desktop, frontend, backend and 00_ASCII_START_HERE together."
    )


def user_log_dir() -> Path:
    override = os.environ.get("LINYUANZHE_LAUNCH_LOG_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", "").strip()
        if base:
            return Path(base).expanduser() / "LinyuanzheDesktop" / "logs"
        return Path.home() / "AppData" / "Roaming" / "LinyuanzheDesktop" / "logs"
    base = os.environ.get("XDG_STATE_HOME", "").strip()
    if base:
        return Path(base).expanduser() / "linyuanzhe_desktop" / "logs"
    return Path.home() / ".local" / "state" / "linyuanzhe_desktop" / "logs"


class TeeLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._fp = None

    def __enter__(self) -> "TeeLogger":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = self.path.open("a", encoding="utf-8", errors="replace")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fp:
            self._fp.close()

    def write(self, text: str = "") -> None:
        print(text, flush=True)
        if self._fp:
            self._fp.write(text + "\n")
            self._fp.flush()


def _public_log_path(path: Path) -> str:
    if platform.system() == "Windows":
        return str(path)
    try:
        return "<user-logs>/" + path.name
    except Exception:
        return "<user-logs>/last_windows_launch.log"


def _entry_args(entry_kind: str, raw_extra: Sequence[str]) -> list[str]:
    args = list(raw_extra)
    # Keep historical BAT semantics.  The generator usually passes these
    # explicitly, but the Python wrapper also protects hand-written BAT copies.
    if entry_kind == "start_desktop_auto" and "--backend-mode" not in args:
        args = ["--backend-mode", "auto", *args]
    elif entry_kind == "start_desktop_provider" and "--backend-mode" not in args:
        args = ["--backend-mode", "provider", *args]
    return args


def _prepare_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["LINYUANZHE_ROOT_HINT"] = str(root)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env.setdefault("PYTHONNOUSERSITE", "1")
    # Keep diagnostics and bridge reports outside the shipped package by default.
    env.setdefault("LINYUANZHE_REPORT_DIR", str(user_log_dir().parent / "reports"))
    return env


def _run_child(cmd: list[str], *, root: Path, env: dict[str, str], log: TeeLogger) -> int:
    start = time.time()
    log.write("[Linyuanzhe] Command: <python> -S -B -u <entry> ...")
    proc = subprocess.Popen(
        cmd,
        cwd=str(root),
        env=env,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            log.write(line.rstrip("\r\n"))
        rc = proc.wait()
    except KeyboardInterrupt:
        log.write("[Linyuanzhe] Interrupted by user.")
        try:
            proc.terminate()
        except Exception:
            pass
        return 130
    elapsed = time.time() - start
    log.write(f"[Linyuanzhe] Child exit code: {rc}; elapsed={elapsed:.2f}s")
    return int(rc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"{VERSION_LABEL} Windows safe launcher")
    parser.add_argument("--entry-kind", required=True)
    parser.add_argument("--python-entry", required=True)
    parser.add_argument("--title", default=VERSION_LABEL)
    parser.add_argument("--python-mode", choices=["plain", "tk"], default="plain")
    parser.add_argument("--launcher-dir", default="")
    parser.add_argument("--start-dir", default="")
    args, extra = parser.parse_known_args(argv)

    log_path = user_log_dir() / "last_windows_launch.log"
    with TeeLogger(log_path) as log:
        log.write("=" * 72)
        log.write(f"{datetime.now().isoformat(timespec='seconds')} {VERSION_LABEL} Windows launch")
        log.write(f"[Linyuanzhe] Title: {args.title}")
        log.write(f"[Linyuanzhe] Python: {sys.executable}")
        log.write(f"[Linyuanzhe] Python version: {sys.version.split()[0]}")
        log.write(f"[Linyuanzhe] Log: {_public_log_path(log_path)}")
        try:
            if not (MIN_PYTHON <= sys.version_info[:2] <= MAX_PYTHON):
                log.write("[Linyuanzhe] Python version unsupported. Install Python 3.10-3.14 from python.org.")
                return 2
            anchor = Path(__file__)
            root = find_project_root(anchor, launcher_dir=args.launcher_dir, start_dir=args.start_dir)
            entry = root / args.python_entry.replace("\\", os.sep).replace("/", os.sep)
            if not entry.exists():
                log.write(f"[Linyuanzhe] Entry file missing: {args.python_entry}")
                return 21
            env = _prepare_env(root)
            log.write("[Linyuanzhe] Root: <package-root>")
            log.write(f"[Linyuanzhe] Entry: {args.python_entry}")
            if args.python_mode == "tk":
                try:
                    import tkinter  # noqa: F401
                    log.write("[Linyuanzhe] tkinter import: PASS")
                except Exception as exc:
                    log.write(f"[Linyuanzhe] tkinter import: FAIL - {exc}")
                    log.write("[Linyuanzhe] Install official Python and enable Tcl/Tk and IDLE.")
                    return 3
            child_args = _entry_args(args.entry_kind, extra)
            cmd = [sys.executable, "-S", "-B", "-u", str(entry), *child_args]
            start = time.time()
            rc = _run_child(cmd, root=root, env=env, log=log)
            elapsed = time.time() - start
            if (
                rc == 0
                and args.entry_kind.startswith("start_desktop")
                and "--self-check" not in child_args
                and "--bridge-only" not in child_args
                and elapsed < 2.0
                and os.environ.get("LINYUANZHE_ALLOW_FAST_SUCCESS", "").strip().lower() not in {"1", "true", "yes", "on"}
            ):
                log.write("[Linyuanzhe] Desktop exited too quickly; treating as startup failure to avoid silent window close.")
                return 90
            return rc
        except Exception as exc:  # noqa: BLE001 - Windows entry boundary
            log.write("[Linyuanzhe] Launcher exception caught.")
            log.write(f"[Linyuanzhe] Error type: {type(exc).__name__}")
            log.write(f"[Linyuanzhe] Error: {exc}")
            if os.environ.get("LINYUANZHE_ENTRY_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
                log.write(traceback.format_exc())
            log.write("[Linyuanzhe] The console is kept open by the BAT wrapper on failure.")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
