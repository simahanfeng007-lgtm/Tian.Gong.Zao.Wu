from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"
SMOKE = FRONTEND_PARENT / "linyuanzhe_frontend" / "run_connector_registry_smoke.py"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.66 MCP / connector registry governance preflight")
    parser.add_argument("--out", default=str(REPORTS / "connector_registry_preflight_l666.json"))
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, str(SMOKE)], cwd=str(FRONTEND_PARENT), env=_env(), text=True, capture_output=True, timeout=120)
    (REPORTS / "l666_connector_registry_smoke.log").write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "smoke stdout was not json"}
    summary = {
        "contract_version": "tiangong.l6_66.connector_registry_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": proc.returncode == 0 and bool(payload.get("ok")),
        "returncode": proc.returncode,
        "smoke_log": str(REPORTS / "l666_connector_registry_smoke.log"),
        "payload": payload,
        "boundaries": {
            "frontend_does_not_install_mcp_server": True,
            "frontend_does_not_execute_connector": True,
            "frontend_does_not_store_connector_secret": True,
            "frontend_does_not_display_raw_endpoint": True,
            "market_install_disabled": True,
            "registry_requests_route_to_runtime_only": True,
            "runtime_quality_gate_workspace_authority_required": True,
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
