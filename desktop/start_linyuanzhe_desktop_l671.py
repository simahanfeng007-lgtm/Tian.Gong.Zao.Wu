from __future__ import annotations

"""Start the bundled local Runtime bridge and the Tk desktop frontend."""

import argparse
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"

URL_RE = re.compile(r"LINYUANZHE_LOCAL_RUNTIME_URL=(http://[^\s]+)")


def _pythonpath() -> str:
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


def _terminate(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception as exc:
            _ = exc
            return


def _start_bridge(args: argparse.Namespace, env: dict[str, str]) -> tuple[subprocess.Popen[str], str]:
    cmd = [sys.executable, str(BRIDGE), "--host", args.host, "--port", str(args.port), "--backend-mode", args.backend_mode, "--timeout", str(args.backend_timeout)]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    assert proc.stdout is not None
    deadline = time.time() + 20
    seen: list[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            seen.append(line.rstrip())
            m = URL_RE.search(line)
            if m:
                return proc, m.group(1)
        if proc.poll() is not None:
            break
    tail = "\n".join(seen[-20:])
    _terminate(proc)
    raise RuntimeError(f"本地桥接服务未能启动。\n{tail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者桌面端前后端一体化启动器 L6.70.1")
    parser.add_argument("--backend-mode", choices=["mock", "provider"], default=os.environ.get("LINYUANZHE_BACKEND_MODE", "mock"), help="mock 为离线可启动模式；provider 使用当前进程内存中的真实模型配置。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--backend-timeout", type=float, default=float(os.environ.get("LINYUANZHE_BACKEND_TIMEOUT", "120") or 120))
    parser.add_argument("--bridge-only", action="store_true", help="只启动本地桥接服务，不打开桌面 UI。")
    args = parser.parse_args(argv)

    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath()
    bridge_proc, runtime_url = _start_bridge(args, env)
    print(f"本地桥接后端已启动：{runtime_url}")
    print("提示：这是桌面一体包的本地桥接，不等同于正式真实 Runtime RC 解阻。")

    if args.bridge_only:
        try:
            bridge_proc.wait()
        finally:
            _terminate(bridge_proc)
        return 0

    try:
        frontend_cmd = [sys.executable, "-m", "linyuanzhe_frontend.app", "--runtime-url", runtime_url]
        return subprocess.call(frontend_cmd, cwd=str(FRONTEND_PARENT), env=env)
    finally:
        _terminate(bridge_proc)


if __name__ == "__main__":
    raise SystemExit(main())
