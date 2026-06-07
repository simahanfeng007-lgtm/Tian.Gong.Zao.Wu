from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linyuanzhe_frontend.clients import RuntimeIntegrationProbe
from linyuanzhe_frontend.contracts.rc_readiness import RcPreflightReport, rc_preflight_policy
from linyuanzhe_frontend.scripts.runtime_contract_server import RuntimeContractServer

ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = ROOT / "reports" / "l6_58_rc_preflight_report.json"
DEFAULT_MESSAGE = "请生成一个三步只读计划：检查运行状态、返回摘要、结束任务。"


def _write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FE.01 STEP19 / L6.58 frontend/backend RC preflight")
    parser.add_argument("--runtime-url", default=os.environ.get("LINYUANZHE_RUNTIME_URL", ""), help="真实 Runtime 网关地址；报告只写 digest，不写明文 URL")
    parser.add_argument("--contract-server", action="store_true", help="强制使用本地受控 Runtime 契约服务器")
    parser.add_argument("--require-real", action="store_true", help="没有真实 Runtime URL 或真实联调未 ready 时返回非零，供 STEP20 合成闸口使用")
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("LINYUANZHE_RUNTIME_TIMEOUT", "8") or 8), help="HTTP/SSE 超时秒数")
    parser.add_argument("--message", default=DEFAULT_MESSAGE, help="只读联调 smoke 消息")
    parser.add_argument("--provider-write-mode", choices=["auto", "fixture", "read_only", "smoke"], default=os.environ.get("LINYUANZHE_PROVIDER_WRITE_MODE", "auto"), help="Provider 设置探测模式；真实 Runtime 默认 read_only，只有 smoke 模式会提交写入。")
    parser.add_argument("--provider-smoke-key", default=os.environ.get("LINYUANZHE_PROVIDER_SMOKE_KEY", ""), help="Provider 写入烟测专用 key；报告不写明文。")
    parser.add_argument("--provider-smoke-base-url", default=os.environ.get("LINYUANZHE_PROVIDER_SMOKE_BASE_URL", ""), help="Provider 写入烟测专用 base URL；报告不写明文。")
    parser.add_argument("--out", default=str(DEFAULT_REPORT), help="输出报告 JSON 路径")
    args = parser.parse_args(argv)

    started_at = datetime.now().isoformat(timespec="seconds")
    runtime_url = str(args.runtime_url or "").strip()
    server = None
    real_runtime_requested = bool(runtime_url) and not args.contract_server
    real_runtime_executed = False
    contract_server_fallback_used = False
    skipped_reason = ""
    mode = "real_runtime"

    if args.contract_server:
        server = RuntimeContractServer().start()
        runtime_url = server.url
        mode = "contract_server"
        contract_server_fallback_used = True
        skipped_reason = "forced contract-server regression mode"
    elif not runtime_url:
        server = RuntimeContractServer().start()
        runtime_url = server.url
        mode = "contract_server"
        contract_server_fallback_used = True
        skipped_reason = "LINYUANZHE_RUNTIME_URL not provided"
    else:
        real_runtime_executed = True

    try:
        provider_write_mode = args.provider_write_mode
        if provider_write_mode == "auto" and mode == "real_runtime":
            provider_write_mode = "read_only"
        probe = RuntimeIntegrationProbe(
            runtime_url,
            timeout=args.timeout,
            mode=mode,
            provider_write_mode=provider_write_mode,
            provider_smoke_key=args.provider_smoke_key,
            provider_smoke_base_url=args.provider_smoke_base_url,
        )
        integration_report = probe.run(args.message)
        preflight = RcPreflightReport.from_integration_report(
            integration_report,
            mode=mode,
            real_runtime_requested=real_runtime_requested,
            real_runtime_executed=real_runtime_executed,
            contract_server_fallback_used=contract_server_fallback_used,
            real_runtime_skipped_reason=skipped_reason,
        )
        payload = preflight.to_dict()
        payload["checked_at"] = started_at
        payload["policy"] = rc_preflight_policy()
        payload["runtime_url_visible"] = "digest_only"
        payload["provider_write_mode"] = provider_write_mode
        payload["provider_write_mutates_real_runtime"] = bool(mode == "real_runtime" and provider_write_mode == "smoke")
        payload["note"] = "本报告不包含 Runtime URL 明文、Provider Key 明文或 Provider Base URL 明文。"
        _write_report(Path(args.out), payload)
        print(json.dumps({"ok": payload["ok"], "ready_for_combine": payload["ready_for_combine"], "rc_status": payload["rc_status"], "mode": mode, "report": str(Path(args.out))}, ensure_ascii=False, indent=2))
        if args.require_real:
            return 0 if payload["ready_for_combine"] else 2
        return 0 if payload["ok"] else 1
    finally:
        if server is not None:
            server.close()


if __name__ == "__main__":
    raise SystemExit(main())
