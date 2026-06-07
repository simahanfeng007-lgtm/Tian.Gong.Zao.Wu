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
SMOKE = FRONTEND_PARENT / "linyuanzhe_frontend" / "run_file_transfer_guide_interrupt_smoke.py"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.64 file transfer / conversation guide / task interrupt preflight")
    parser.add_argument("--out", default=str(REPORTS / "file_transfer_interrupt_preflight_l664.json"))
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, str(SMOKE)], cwd=str(FRONTEND_PARENT), env=_env(), text=True, capture_output=True, timeout=120)
    (REPORTS / "l664_file_transfer_interrupt_smoke.log").write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "smoke stdout was not json"}
    summary = {
        "contract_version": "tiangong.l6_64.file_transfer_guide_interrupt_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": proc.returncode == 0 and bool(payload.get("ok")),
        "returncode": proc.returncode,
        "smoke_log": str(REPORTS / "l664_file_transfer_interrupt_smoke.log"),
        "payload": payload,
        "boundaries": {
            "file_transfer_route_to_runtime_only": True,
            "frontend_does_not_execute_tools": True,
            "frontend_does_not_write_memory": True,
            "frontend_does_not_write_audit": True,
            "frontend_does_not_apply_rollback": True,
            "interrupt_is_control_request_only": True,
            "conversation_guide_is_user_confirmed_prompt_only": True,
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
