from __future__ import annotations

"""天工造物 v2.0 临渊者 - 一键依赖检测安装
检测 Python 版本、tkinter、标准库完整性，给出中文诊断。
零第三方依赖，无需 pip install。
"""

import sys
import importlib
from pathlib import Path

REQUIRED_MODULES = [
    "tkinter",
    "json", "re", "os", "sys", "time", "math", "hashlib",
    "dataclasses", "enum", "pathlib", "argparse", "subprocess",
    "threading", "queue", "collections", "typing", "uuid",
    "xml.etree.ElementTree", "ast", "shlex", "socket",
    "urllib.request", "signal",
]

MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 14)  # 3.14 在 Linux 已验证可用，Windows 请用 3.12

def _p(v: tuple) -> str:
    return ".".join(map(str, v))

def check_python() -> tuple[bool, str]:
    v = sys.version_info[:2]
    ver_str = sys.version.split()[0]
    if v < MIN_PYTHON:
        return False, f"Python {ver_str} 太旧，需要 ≥ {_p(MIN_PYTHON)}。请安装 Python {_p(MIN_PYTHON)} 或更新。"
    if v > MAX_PYTHON:
        return False, f"Python {ver_str} 太新（{_p(MAX_PYTHON)} 是已验证上限）。如遇问题请降级到 {_p(MIN_PYTHON)}-{_p(MAX_PYTHON)}。"
    return True, ver_str

def check_tkinter() -> tuple[bool, str]:
    try:
        import tkinter
        return True, f"tkinter {tkinter.TkVersion}"
    except ImportError:
        return False, "未安装 tkinter。安装 Python 时请勾选「tcl/tk and IDLE」。"

def check_modules() -> list[tuple[str, bool, str]]:
    results = []
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            results.append((name, True, "ok"))
        except ImportError as e:
            results.append((name, False, str(e)))
    return results

def main() -> int:
    print("天工造物 v2.0 - 临渊者  依赖检测")
    print("-" * 40)

    py_ok, py_msg = check_python()
    print(f"Python    : {'PASS' if py_ok else 'FAIL'} · {py_msg}")

    tk_ok, tk_msg = check_tkinter()
    print(f"tkinter   : {'PASS' if tk_ok else 'FAIL'} · {tk_msg}")

    failed = not py_ok or not tk_ok
    module_results = check_modules()
    for name, ok, msg in module_results:
        if not ok:
            print(f"  {name:<30} FAIL · {msg}")
            failed = True

    ok_count = sum(1 for _, ok, _ in module_results if ok)
    fail_count = len(module_results) - ok_count
    print(f"\n标准库模块: {ok_count}/{len(module_results)} 可用" + (f"，{fail_count} 缺失" if fail_count else ""))

    print("-" * 40)
    if failed:
        print("\n诊断建议：")
        if not py_ok:
            print(f"  → 安装 Python {_p(MIN_PYTHON)}-{_p(MAX_PYTHON)}: https://www.python.org/downloads/")
        if not tk_ok:
            print("  → 重新运行 Python 安装程序，勾选「tcl/tk and IDLE」")
        if fail_count:
            print("  → 标准库模块缺失，请重新安装 Python（不要用精简版）")
        print("\n按任意键退出...")
        return 1

    print(f"全部通过。Python 环境就绪。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
