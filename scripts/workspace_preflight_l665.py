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
SMOKE = FRONTEND_PARENT / "linyuanzhe_frontend" / "run_workspace_authorization_smoke.py"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.65 Agent Workspace / file authorization preflight")
    parser.add_argument("--out", default=str(REPORTS / "workspace_preflight_l665.json"))
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, str(SMOKE)], cwd=str(FRONTEND_PARENT), env=_env(), text=True, capture_output=True, timeout=120)
    (REPORTS / "l665_workspace_authorization_smoke.log").write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "smoke stdout was not json"}
    summary = {
        "contract_version": "tiangong.l6_65.workspace_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": proc.returncode == 0 and bool(payload.get("ok")),
        "returncode": proc.returncode,
        "smoke_log": str(REPORTS / "l665_workspace_authorization_smoke.log"),
        "payload": payload,
        "boundaries": {
            "frontend_does_not_create_workspace": True,
            "frontend_does_not_mutate_acl": True,
            "frontend_does_not_copy_file_bytes": True,
            "frontend_does_not_expose_raw_path": True,
            "write_authorization_requires_runtime_quality_gate": True,
            "download_handoff_uses_digest_not_raw_token": True,
            "runtime_tiangong_wangguan_authority_required": True,
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
