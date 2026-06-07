from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"
FRONTEND = FRONTEND_PARENT / "linyuanzhe_frontend"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _pythonpath(extra: list[Path]) -> str:
    current = os.environ.get("PYTHONPATH", "")
    values = [str(p) for p in extra]
    if current:
        values.append(current)
    return os.pathsep.join(values)


def _run_backend_status() -> int:
    cmd = [sys.executable, str(BACKEND / "run_agent.py"), "--mock", "--status"]
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath([BACKEND])
    proc = subprocess.run(cmd, cwd=str(BACKEND), env=env, text=True, capture_output=True, timeout=20)
    if proc.returncode == 0:
        print("backend_status=ok")
    else:
        print("backend_status=failed")
        if proc.stderr:
            print(proc.stderr[-1000:])
    return proc.returncode


def _start_contract_server(env: dict[str, str]) -> subprocess.Popen:
    cmd = [sys.executable, "-m", "linyuanzhe_frontend.scripts.runtime_contract_server", "--host", "127.0.0.1", "--port", "0"]
    proc = subprocess.Popen(cmd, cwd=str(FRONTEND_PARENT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # The bundled contract server module is primarily used by preflight. For desktop fallback, use the public run_rc_preflight path instead.
    return proc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者 FE01 STEP31 / L6.70 RC 统一启动器")
    parser.add_argument("--mode", choices=["auto", "real", "contract"], default="auto", help="real 使用外部 Runtime URL；contract 只启动本地契约演示，不代表真实联调。")
    parser.add_argument("--preflight-only", action="store_true", help="只运行 RC preflight，不打开桌面前端。")
    parser.add_argument("--real-gate", action="store_true", help="运行 L6.61 真实 Runtime 解阻闸口；缺少真实地址时阻断。")
    parser.add_argument("--observability-preflight", action="store_true", help="运行 L6.62 运行观测台只读预检。")
    parser.add_argument("--hookbus-preflight", action="store_true", help="运行 L6.63 HookBus 确定性规则层预检。")
    parser.add_argument("--file-transfer-preflight", action="store_true", help="运行 L6.64 文件传输/对话引导/中断任务预检。")
    parser.add_argument("--workspace-preflight", action="store_true", help="运行 L6.65 Agent Workspace / 文件授权预检。")
    parser.add_argument("--connector-preflight", action="store_true", help="运行 L6.66 MCP / 连接器注册表预检。")
    parser.add_argument("--session-manager-preflight", action="store_true", help="运行 L6.67 多任务 Session 管理器预检。")
    parser.add_argument("--installer-rc-preflight", action="store_true", help="运行 L6.68 安装器 RC 前置结构预检。")
    parser.add_argument("--packager-preflight", action="store_true", help="运行 L6.69 Windows 打包器 dry-run / 发布管线预检。")
    parser.add_argument("--real-runtime-smoke-l670", action="store_true", help="运行 L6.70 真实 Runtime endpoint smoke；缺少 Runtime URL 时阻断。")
    parser.add_argument("--verify-l670", action="store_true", help="运行 L6.70 release verifier。")
    parser.add_argument("--verify-l669", action="store_true", help="兼容运行 L6.69 release verifier。")
    parser.add_argument("--verify-l668", action="store_true", help="兼容运行 L6.68 release verifier。")
    parser.add_argument("--verify-l667", action="store_true", help="兼容运行 L6.67 release verifier。")
    parser.add_argument("--verify-l666", action="store_true", help="兼容运行 L6.66 release verifier。")
    parser.add_argument("--runtime-url", default="", help="临时传入真实 Runtime 地址；不打印明文，只传给子进程。")
    parser.add_argument("--skip-backend-status", action="store_true", help="跳过本地 Runtime 包导入/status 检查。")
    args = parser.parse_args(argv)

    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath([BACKEND, FRONTEND_PARENT])
    if args.runtime_url:
        env["LINYUANZHE_RUNTIME_URL"] = args.runtime_url.strip()
    runtime_url = env.get("LINYUANZHE_RUNTIME_URL", "").strip()

    if not args.skip_backend_status:
        status_code = _run_backend_status()
        if status_code != 0:
            return status_code

    if args.real_gate:
        cmd = [sys.executable, str(ROOT / "scripts" / "real_runtime_unlock_l661.py"), "--require-real"]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.observability_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "observability_preflight_l662.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.hookbus_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "hookbus_preflight_l663.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.file_transfer_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "file_transfer_interrupt_preflight_l664.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.workspace_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "workspace_preflight_l665.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.connector_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "connector_registry_preflight_l666.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.session_manager_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "session_manager_preflight_l667.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.installer_rc_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "installer_rc_preflight_l668.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.packager_preflight:
        cmd = [sys.executable, str(ROOT / "scripts" / "package_builder_preflight_l669.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.real_runtime_smoke_l670:
        cmd = [sys.executable, str(ROOT / "scripts" / "real_runtime_endpoint_smoke_l670.py"), "--require-real"]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.verify_l670:
        cmd = [sys.executable, str(ROOT / "scripts" / "verify_l670_release.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.verify_l669:
        cmd = [sys.executable, str(ROOT / "scripts" / "verify_l669_release.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.verify_l668:
        cmd = [sys.executable, str(ROOT / "scripts" / "verify_l668_release.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.verify_l667:
        cmd = [sys.executable, str(ROOT / "scripts" / "verify_l667_release.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)
    if args.verify_l666:
        cmd = [sys.executable, str(ROOT / "scripts" / "verify_l666_release.py")]
        return subprocess.call(cmd, cwd=str(ROOT), env=env)

    if args.preflight_only:
        if args.mode == "real":
            cmd = [sys.executable, str(ROOT / "scripts" / "real_runtime_unlock_l661.py"), "--require-real"]
            return subprocess.call(cmd, cwd=str(ROOT), env=env)
        cmd = [sys.executable, str(ROOT / "scripts" / "rc_preflight_l659.py")]
        if args.mode == "contract":
            cmd.append("--contract-server")
        return subprocess.call(cmd, cwd=str(ROOT), env=env)

    if args.mode == "real" and not runtime_url:
        print("blocked=LINYUANZHE_RUNTIME_URL not provided")
        return 2
    if args.mode == "real":
        gate = [sys.executable, str(ROOT / "scripts" / "real_runtime_unlock_l661.py"), "--require-real"]
        gate_code = subprocess.call(gate, cwd=str(ROOT), env=env)
        if gate_code != 0:
            return gate_code
    if args.mode == "auto" and runtime_url:
        print(f"runtime_url_digest={_digest(runtime_url)}")
        print("launch_mode=real_runtime_frontend")
        cmd = [sys.executable, "-m", "linyuanzhe_frontend.app"]
        return subprocess.call(cmd, cwd=str(FRONTEND_PARENT), env=env)

    print("launch_mode=contract_server_demo")
    print("notice=contract mode is UI/endpoint regression only; it is not a real Runtime smoke result")
    cmd = [sys.executable, "-m", "linyuanzhe_frontend.run_rc_preflight", "--contract-server"]
    code = subprocess.call(cmd, cwd=str(FRONTEND_PARENT), env=env)
    if code != 0:
        return code
    demo = [sys.executable, "-m", "linyuanzhe_frontend.run_desktop_demo"]
    return subprocess.call(demo, cwd=str(FRONTEND_PARENT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
