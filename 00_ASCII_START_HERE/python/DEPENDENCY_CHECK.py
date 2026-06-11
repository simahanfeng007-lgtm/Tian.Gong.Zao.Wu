from __future__ import annotations

"""天工造物 v2.0 临渊者 - 一键依赖检测安装。"""

import argparse
import importlib
import os
import sys

REQUIRED_MODULES = ["tkinter", "json", "re", "os", "sys", "time", "math", "hashlib", "dataclasses", "enum", "pathlib", "argparse", "subprocess", "threading", "queue", "collections", "typing", "uuid", "xml.etree.ElementTree", "ast", "shlex", "socket", "urllib.request", "signal"]
MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 14)


def check_module(name: str):
    try:
        importlib.import_module(name)
        return True, "ok"
    except Exception as exc:
        return False, repr(exc)


def check_tkinter_display():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return True, "Tk root created"
    except Exception as exc:
        return False, repr(exc)


def _wait_on_failure() -> None:
    try:
        input("依赖检测未通过，按回车键退出...")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-display", action="store_true")
    args = parser.parse_args(argv)
    print("[临渊者] FE01 STEP68 / L6.73.8 - 一键自检")
    ok_py = MIN_PYTHON <= sys.version_info[:2] <= MAX_PYTHON
    print(f"python_version       : {'PASS' if ok_py else 'FAIL'} · {sys.version.split()[0]}")
    all_ok = ok_py
    for module in REQUIRED_MODULES:
        ok, msg = check_module(module)
        label = "tkinter_import" if module == "tkinter" else module
        print(f"{label:21}: {'PASS' if ok else 'FAIL'} · {msg}")
        all_ok = all_ok and ok
    if args.require_display:
        ok, msg = check_tkinter_display()
        print(f"tkinter_display      : {'PASS' if ok else 'FAIL'} · {msg}")
        all_ok = all_ok and ok
    else:
        msg = "未验证 DISPLAY；如需桌面显示验收请运行 --require-display 或 xvfb-run。" if (not sys.platform.startswith("win") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))) else "未创建 Tk root；如需严格验收请运行 --require-display。"
        print(f"tkinter_display      : SKIP · {msg}")
    if not all_ok:
        _wait_on_failure()
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
