from __future__ import annotations

"""Start the bundled local Runtime bridge and the Tk desktop frontend.

FE01 STEP31Q / L6.71.7 makes this Python launcher the single source of truth
for Windows, macOS and Linux. OS-specific files are now thin wrappers only.
"""

import argparse
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from platform_runtime_l6709 import (
    is_supported_desktop_platform,
    merged_pythonpath,
    platform_name,
    project_root,
    provider_config_path,
    reports_dir,
    terminate_process,
    tk_preflight_message,
)

ROOT = project_root()
FRONTEND_PARENT = ROOT / "frontend"
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
URL_RE = re.compile(r"LINYUANZHE_LOCAL_RUNTIME_URL=(http://[^\s]+)")


def _write_startup_failure_report(message: str) -> None:
    try:
        report = reports_dir(ROOT) / "desktop_startup_failure_l6710.txt"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(message, encoding="utf-8")
        print(f"启动失败报告：{report}")
    except Exception:
        return


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = merged_pythonpath(ROOT)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _start_bridge(args: argparse.Namespace, env: dict[str, str]) -> tuple[subprocess.Popen[str], str]:
    cmd = [
        sys.executable,
        str(BRIDGE),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--backend-mode",
        args.backend_mode,
        "--timeout",
        str(args.backend_timeout),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert proc.stdout is not None
    lines: queue.Queue[str] = queue.Queue()
    url_box: dict[str, str] = {}

    def drain() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            clean = line.rstrip()
            lines.put(clean)
            match = URL_RE.search(clean)
            if match:
                url_box["url"] = match.group(1)
            if args.bridge_log:
                print(clean)

    threading.Thread(target=drain, name="linyuanzhe-bridge-stdout", daemon=True).start()
    deadline = time.time() + max(5, int(args.startup_timeout))
    seen: list[str] = []
    while time.time() < deadline:
        while True:
            try:
                seen.append(lines.get_nowait())
            except queue.Empty:
                break
        if url_box.get("url"):
            return proc, url_box["url"]
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    while True:
        try:
            seen.append(lines.get_nowait())
        except queue.Empty:
            break
    tail = "\n".join(seen[-30:])
    terminate_process(proc)
    raise RuntimeError(f"本地桥接服务未能启动。\n{tail}")


def _run_self_check(require_display: bool = False) -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("platform", is_supported_desktop_platform(), platform_name()))
    checks.append(("python_version", sys.version_info >= (3, 10), sys.version.split()[0]))
    checks.append(("project_root", (ROOT / "frontend" / "linyuanzhe_frontend" / "app.py").exists(), str(ROOT)))
    checks.append(("bridge_entry", BRIDGE.exists(), str(BRIDGE.relative_to(ROOT)) if BRIDGE.exists() else str(BRIDGE)))
    checks.append(("provider_config_path", True, str(provider_config_path())))
    tk_error = tk_preflight_message(require_display=require_display)
    checks.append(("tkinter", not tk_error, "ok" if not tk_error else tk_error.splitlines()[-1]))
    max_name = max(len(item[0]) for item in checks)
    failed = False
    for name, ok, message in checks:
        failed = failed or not ok
        print(f"{name:<{max_name}} : {'PASS' if ok else 'FAIL'} · {message}")
    if failed and tk_error:
        _write_startup_failure_report(tk_error)
    return 1 if failed else 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者桌面端三端通用启动器 FE01 STEP31Q / L6.71.7")
    parser.add_argument("--backend-mode", choices=["auto", "mock", "provider"], default=os.environ.get("LINYUANZHE_BACKEND_MODE", "auto"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--backend-timeout", type=float, default=float(os.environ.get("LINYUANZHE_BACKEND_TIMEOUT", "120") or 120))
    parser.add_argument("--startup-timeout", type=float, default=float(os.environ.get("LINYUANZHE_STARTUP_TIMEOUT", "25") or 25))
    parser.add_argument("--bridge-only", action="store_true", help="只启动本地桥接服务，不打开桌面 UI。")
    parser.add_argument("--bridge-log", action="store_true", help="打印桥接服务 stdout，便于诊断。")
    parser.add_argument("--self-check", action="store_true", help="只运行三端通用启动自检。")
    parser.add_argument("--self-check-display", action="store_true", help="自检时同时创建 Tk 窗口验证显示环境。")
    args = parser.parse_args(argv)

    if args.self_check:
        return _run_self_check(require_display=args.self_check_display)

    if not is_supported_desktop_platform():
        message = f"当前平台未列入桌面交付目标：{platform_name()}；目标为 Windows/macOS/Linux。"
        print(message)
        _write_startup_failure_report(message)
        return 11

    if not args.bridge_only:
        tk_error = tk_preflight_message(require_display=True)
        if tk_error:
            print(tk_error)
            _write_startup_failure_report(tk_error)
            return 12

    env = _build_env()
    bridge_proc, runtime_url = _start_bridge(args, env)
    print(f"本地桥接后端已启动：{runtime_url}")
    print("提示：这是桌面一体包的本地桥接，不等同于正式真实 Runtime RC 解阻。")

    if args.bridge_only:
        try:
            bridge_proc.wait()
        finally:
            terminate_process(bridge_proc)
        return 0

    try:
        frontend_cmd = [sys.executable, "-m", "linyuanzhe_frontend.app", "--runtime-url", runtime_url]
        return subprocess.call(frontend_cmd, cwd=str(FRONTEND_PARENT), env=env)
    finally:
        terminate_process(bridge_proc)


if __name__ == "__main__":
    raise SystemExit(main())
