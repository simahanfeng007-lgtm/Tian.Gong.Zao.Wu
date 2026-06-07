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
from linyuanzhe_frontend.contracts.integration_smoke import integration_smoke_policy
from linyuanzhe_frontend.scripts.runtime_contract_server import RuntimeContractServer

ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = ROOT / "reports" / "l6_58_real_runtime_e2e_smoke_report.json"
DEFAULT_MESSAGE = "请生成一个三步只读计划：检查运行状态、返回摘要、结束任务。"


def _write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FE.01 STEP19 / L6.58 frontend/backend E2E smoke")
    parser.add_argument("--runtime-url", default=os.environ.get("LINYUANZHE_RUNTIME_URL", ""), help="真实 Runtime 网关地址；报告只写 digest，不写明文 URL")
    parser.add_argument("--contract-server", action="store_true", help="强制使用本地受控 Runtime 契约服务器")
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("LINYUANZHE_RUNTIME_TIMEOUT", "8") or 8), help="HTTP/SSE 超时秒数")
    parser.add_argument("--message", default=DEFAULT_MESSAGE, help="只读联调 smoke 消息")
    parser.add_argument("--out", default=str(DEFAULT_REPORT), help="输出报告 JSON 路径")
    args = parser.parse_args(argv)

    started_at = datetime.now().isoformat(timespec="seconds")
    server = None
    mode = "real_runtime"
    runtime_url = str(args.runtime_url or "").strip()
    if args.contract_server or not runtime_url:
        server = RuntimeContractServer().start()
        runtime_url = server.url
        mode = "contract_server"

    try:
        probe = RuntimeIntegrationProbe(runtime_url, timeout=args.timeout, mode=mode)
        report = probe.run(args.message)
        payload = report.to_dict()
        payload["checked_at"] = started_at
        payload["policy"] = integration_smoke_policy()
        payload["runtime_url_visible"] = "digest_only"
        payload["note"] = "本报告不包含 Runtime URL 明文、Provider Key 明文或 Provider Base URL 明文。"
        _write_report(Path(args.out), payload)
        print(json.dumps({"ok": payload["ok"], "mode": mode, "report": str(Path(args.out))}, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 1
    finally:
        if server is not None:
            server.close()


if __name__ == "__main__":
    raise SystemExit(main())
