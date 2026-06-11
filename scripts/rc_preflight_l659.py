from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"
REPORTS = ROOT / "reports"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _backend_static_check() -> dict:
    sys.path.insert(0, str(BACKEND))
    from tiangong_agent_runtime import __version__, build_product_identity_public
    from tiangong_agent_runtime.frontend_contract import build_frontend_backend_contract, validate_frontend_contract

    identity = build_product_identity_public()
    contract = build_frontend_backend_contract()
    check = validate_frontend_contract()
    return {
        "ok": bool(check.ok and identity.get("unique_developer") == "于泳翔" and identity.get("angel_investor") == "胖胖龙"),
        "runtime_version": __version__,
        "product_identity_ok": identity.get("unique_developer") == "于泳翔" and identity.get("angel_investor") == "胖胖龙",
        "canonical_entry": contract.get("canonical_entry"),
        "chat_stream_endpoint": contract.get("chat_stream_endpoint"),
        "terminal_order": contract.get("sse_schema", {}).get("terminal_order"),
        "frontend_contract_ok": bool(check.ok),
        "frontend_contract_issues": list(check.issues),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="L6.59 前后端合成 RC preflight")
    parser.add_argument("--contract-server", action="store_true", help="强制使用本地契约服务器；不代表真实 Runtime 联调。")
    parser.add_argument("--require-real", action="store_true", help="要求真实 Runtime URL 与 ready_for_combine。")
    parser.add_argument("--timeout", default=os.environ.get("LINYUANZHE_RUNTIME_TIMEOUT", "8"), help="传给前端 RC preflight 的 HTTP/SSE 超时秒数。")
    parser.add_argument("--message", default="", help="传给前端 RC preflight 的只读 smoke 消息；为空则使用前端默认。")
    parser.add_argument(
        "--provider-write-mode",
        choices=["auto", "fixture", "read_only", "smoke"],
        default=os.environ.get("LINYUANZHE_PROVIDER_WRITE_MODE", "auto"),
        help="Provider 设置探测模式；真实 Runtime 默认 read_only，只有 smoke 模式会提交写入。",
    )
    parser.add_argument("--provider-smoke-key", default=os.environ.get("LINYUANZHE_PROVIDER_SMOKE_KEY", ""), help="Provider 写入烟测专用 key；报告不写明文。")
    parser.add_argument("--provider-smoke-base-url", default=os.environ.get("LINYUANZHE_PROVIDER_SMOKE_BASE_URL", ""), help="Provider 写入烟测专用 base URL；报告不写明文。")
    parser.add_argument("--out", default=str(REPORTS / "rc_preflight_l659.json"))
    args = parser.parse_args(argv)

    REPORTS.mkdir(parents=True, exist_ok=True)
    runtime_url = os.environ.get("LINYUANZHE_RUNTIME_URL", "").strip()
    inner = REPORTS / "rc_preflight_l659_inner.json"
    cmd = [
        sys.executable,
        "-m",
        "linyuanzhe_frontend.run_rc_preflight",
        "--out",
        str(inner),
        "--timeout",
        str(args.timeout or "8"),
        "--provider-write-mode",
        args.provider_write_mode,
    ]
    if args.message:
        cmd.extend(["--message", args.message])
    if args.provider_smoke_key:
        cmd.extend(["--provider-smoke-key", args.provider_smoke_key])
    if args.provider_smoke_base_url:
        cmd.extend(["--provider-smoke-base-url", args.provider_smoke_base_url])
    if args.contract_server or not runtime_url:
        cmd.append("--contract-server")
    if args.require_real:
        cmd.append("--require-real")

    env = _env()
    env["LINYUANZHE_PROVIDER_WRITE_MODE"] = args.provider_write_mode
    if args.provider_smoke_key:
        env["LINYUANZHE_PROVIDER_SMOKE_KEY"] = args.provider_smoke_key
    if args.provider_smoke_base_url:
        env["LINYUANZHE_PROVIDER_SMOKE_BASE_URL"] = args.provider_smoke_base_url
    proc = subprocess.run(cmd, cwd=str(FRONTEND_PARENT), env=env, text=True, capture_output=True, timeout=max(60, int(float(args.timeout or 8) * 10)))
    backend = _backend_static_check()
    inner_payload = json.loads(inner.read_text(encoding="utf-8")) if inner.exists() else {}
    blockers = list(inner_payload.get("merge_blockers") or [])
    if not runtime_url and "real Runtime instance smoke not executed" not in blockers:
        blockers.append("real Runtime instance smoke not executed")

    payload = {
        "contract_version": "tiangong.l6_59.frontend_backend_combine_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "backend_static_check": backend,
        "frontend_runtime_preflight": inner_payload,
        "runtime_url_visible": "digest_only",
        "runtime_url_digest": _digest(runtime_url) if runtime_url else "",
        "real_runtime_url_present": bool(runtime_url),
        "real_runtime_executed": bool(inner_payload.get("real_runtime_executed")),
        "contract_server_used": bool(inner_payload.get("contract_server_fallback_used")),
        "ready_for_combine": bool(backend.get("ok") and inner_payload.get("ready_for_combine")),
        "ok": bool(backend.get("ok") and inner_payload.get("ok")),
        "merge_blockers": blockers,
        "provider_write_mode": args.provider_write_mode,
        "provider_write_mutates_real_runtime": bool(runtime_url and args.provider_write_mode == "smoke"),
        "wrapper_accepts_provider_write_mode": True,
        "note": "不记录 Runtime URL 明文、Provider Key 明文或 Provider Base URL 明文。",
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "ready_for_combine": payload["ready_for_combine"], "real_runtime_executed": payload["real_runtime_executed"], "report": str(Path(args.out))}, ensure_ascii=False, indent=2))
    if args.require_real and not payload["ready_for_combine"]:
        return 2
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
