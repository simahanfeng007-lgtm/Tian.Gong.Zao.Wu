from __future__ import annotations

"""L6.73.8 Python executable probe for launch wrappers."""

import argparse
import os
import sys

MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 14)


def _display_hint_needed() -> bool:
    return False if sys.platform.startswith("win") else not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--require-tk", action="store_true")
    p.add_argument("--require-display", action="store_true")
    args, _ = p.parse_known_args(argv)
    if not (MIN_PYTHON <= sys.version_info[:2] <= MAX_PYTHON):
        print(f"PYTHON_PROBE FAIL: Python {sys.version_info.major}.{sys.version_info.minor}")
        return 2
    print(f"PYTHON_PROBE PASS: Python {sys.version.split()[0]}")
    if args.require_tk or args.require_display:
        try:
            import tkinter as tk  # noqa: F401
            print("TKINTER_IMPORT PASS: tkinter import ok")
        except Exception as exc:
            print(f"TKINTER_IMPORT FAIL: {exc}")
            return 3
    if args.require_display:
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            root.update_idletasks()
            root.destroy()
            print("TKINTER_DISPLAY PASS: Tk root created")
        except Exception as exc:
            print(f"TKINTER_DISPLAY FAIL: {exc}")
            return 4
    elif args.require_tk and _display_hint_needed():
        print("TKINTER_DISPLAY SKIP: tkinter import 可用，但未验证 DISPLAY；如需桌面显示验收请运行 --require-display 或 xvfb-run。")
    print(f"LINYUANZHE_PY_OK={sys.executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
