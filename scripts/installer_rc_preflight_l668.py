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
SMOKE = FRONTEND_PARENT / "linyuanzhe_frontend" / "run_installer_rc_smoke.py"
STARTUP = ROOT / "installer" / "startup" / "startup_self_check_l668.py"
OFFLINE_REPAIR = ROOT / "installer" / "recovery" / "offline_repair_l668.py"
ROLLBACK_PLAN = ROOT / "installer" / "recovery" / "rollback_slot_restore_l668.py"
MANIFEST = ROOT / "installer" / "installer_manifest_l668.json"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _run(name: str, cmd: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), env=_env(), text=True, capture_output=True, timeout=120)
    log = REPORTS / f"l668_{name}.log"
    log.write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "stdout was not json"}
    return {"name": name, "returncode": proc.returncode, "ok": proc.returncode == 0 and bool(payload.get("ok", True)), "log": str(log), "payload": payload}


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.68 installer RC pre-stage preflight")
    parser.add_argument("--out", default=str(REPORTS / "installer_rc_preflight_l668.json"))
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    runs = [
        _run("installer_rc_smoke", [sys.executable, str(SMOKE)], FRONTEND_PARENT),
        _run("startup_self_check", [sys.executable, str(STARTUP)], ROOT),
        _run("offline_repair_dry_run", [sys.executable, str(OFFLINE_REPAIR)], ROOT),
        _run("rollback_plan", [sys.executable, str(ROLLBACK_PLAN)], ROOT),
    ]
    manifest_ok = False
    manifest_summary: dict[str, Any] = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            manifest_ok = (
                manifest.get("contract_version") == "tiangong.l6_68.installer_rc.v1"
                and manifest.get("unique_developer") == "于泳翔"
                and manifest.get("angel_investor") == "胖胖龙"
                and manifest.get("installer_build_allowed") is False
                and manifest.get("updater_skeleton_only") is True
            )
            manifest_summary = {
                "contract_version": manifest.get("contract_version"),
                "version_label": manifest.get("version_label"),
                "slot_count": len(manifest.get("slots", []) or []),
                "startup_check_count": len(manifest.get("startup_checks", []) or []),
                "installer_build_allowed": manifest.get("installer_build_allowed"),
                "updater_skeleton_only": manifest.get("updater_skeleton_only"),
            }
        except Exception as exc:
            manifest_summary = {"read_error": str(exc)[:160]}
    summary = {
        "contract_version": "tiangong.l6_68.installer_rc_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": all(item["ok"] for item in runs) and manifest_ok,
        "manifest_ok": manifest_ok,
        "manifest_summary": manifest_summary,
        "runs": runs,
        "boundaries": {
            "not_final_installer": True,
            "frontend_does_not_build_installer": True,
            "frontend_does_not_apply_update": True,
            "frontend_does_not_restore_rollback_slot": True,
            "frontend_does_not_upload_crash_report": True,
            "offline_repair_defaults_to_dry_run": True,
            "runtime_core_not_mutated": True,
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
