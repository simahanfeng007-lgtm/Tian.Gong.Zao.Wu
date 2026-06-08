from __future__ import annotations

"""Cross-platform desktop runtime helpers for FE01 STEP31Q / L6.71.7.

The desktop package must be launched on Windows, macOS and Linux without
changing Runtime semantics. This module centralizes platform differences that
previous hotfixes handled in scattered platform wrappers.
"""

import os
import platform
import signal
import sys
from pathlib import Path
from typing import Iterable

APP_DIR_NAME = "LinyuanzheDesktop"
APP_DIR_NAME_POSIX = "linyuanzhe_desktop"
SUPPORTED_PLATFORM_NAMES = {"Windows", "Darwin", "Linux"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def platform_name() -> str:
    return platform.system() or sys.platform


def is_supported_desktop_platform() -> bool:
    return platform_name() in SUPPORTED_PLATFORM_NAMES


def user_config_dir() -> Path:
    """Return a writable per-user config directory with no extra dependency."""
    override = os.environ.get("LINYUANZHE_PROVIDER_CONFIG_FILE", "").strip()
    if override:
        return Path(override).expanduser().resolve().parent
    system = platform_name()
    home = Path.home()
    if system == "Windows":
        base = os.environ.get("APPDATA", "").strip()
        return Path(base).expanduser() / APP_DIR_NAME if base else home / "AppData" / "Roaming" / APP_DIR_NAME
    if system == "Darwin":
        return home / "Library" / "Application Support" / APP_DIR_NAME
    base = os.environ.get("XDG_CONFIG_HOME", "").strip()
    return (Path(base).expanduser() if base else home / ".config") / APP_DIR_NAME_POSIX


def provider_config_path() -> Path:
    override = os.environ.get("LINYUANZHE_PROVIDER_CONFIG_FILE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return user_config_dir() / "provider_config.json"


def reports_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "reports"


def pythonpath_parts(root: Path | None = None) -> list[str]:
    base = root or project_root()
    return [str(base / "backend" / "project"), str(base / "frontend")]


def merged_pythonpath(root: Path | None = None, extra: Iterable[str] = ()) -> str:
    parts = pythonpath_parts(root)
    parts.extend(str(x) for x in extra if str(x))
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


def seed_tcl_tk_env() -> None:
    """Point tkinter at bundled Tcl/Tk folders when they exist.

    This does not vendor Tk. It only repairs common Python installs where the
    library directories exist but TCL_LIBRARY/TK_LIBRARY were not seeded.
    """
    base_candidates = [Path(sys.base_prefix), Path(sys.prefix)]
    version_candidates = [("tcl9.0", "tk9.0"), ("tcl8.7", "tk8.7"), ("tcl8.6", "tk8.6")]
    for base in base_candidates:
        for tcl_name, tk_name in version_candidates:
            for parent in (base / "tcl", base / "Lib", base / "lib"):
                tcl_dir = parent / tcl_name
                tk_dir = parent / tk_name
                if tcl_dir.exists() and tk_dir.exists():
                    os.environ.setdefault("TCL_LIBRARY", str(tcl_dir))
                    os.environ.setdefault("TK_LIBRARY", str(tk_dir))
                    return


def tk_preflight_message(*, require_display: bool = True) -> str:
    if sys.version_info < (3, 10):
        return f"当前 Python 版本过低：{sys.version.split()[0]}；需要 Python 3.10+。"
    seed_tcl_tk_env()
    try:
        import tkinter as tk  # noqa: PLC0415
        if require_display:
            root = tk.Tk()
            root.withdraw()
            root.update_idletasks()
            root.destroy()
        return ""
    except Exception as exc:
        return (
            "Tk 桌面依赖不可用，已阻止前端闪退。\n"
            f"Platform={platform.platform()}\n"
            f"Python={sys.executable}\n"
            f"Version={sys.version.split()[0]}\n"
            f"TCL_LIBRARY={os.environ.get('TCL_LIBRARY', '<unset>')}\n"
            f"TK_LIBRARY={os.environ.get('TK_LIBRARY', '<unset>')}\n"
            f"Error={exc}\n"
            "处理方式：Windows 安装官方 Python 3.10/3.11/3.12 并勾选 Tcl/Tk；"
            "macOS 优先使用 python.org 或 Homebrew 的 python3-tk；Linux 安装 python3-tk/tk 包。"
        )


def terminate_process(proc: object, timeout: float = 5.0) -> None:
    """Best-effort terminate for subprocess.Popen-like objects."""
    poll = getattr(proc, "poll", None)
    if callable(poll) and poll() is not None:
        return
    try:
        if os.name == "nt":
            getattr(proc, "terminate")()
        else:
            getattr(proc, "send_signal")(signal.SIGTERM)
        getattr(proc, "wait")(timeout=timeout)
    except Exception:
        try:
            getattr(proc, "kill")()
        except Exception:
            return
