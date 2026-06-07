from __future__ import annotations

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


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _run(name: str, cmd: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), env=_env(), text=True, capture_output=True, timeout=180)
    log = REPORTS / f"l669_{name}.log"
    log.write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "stdout was not json"}
    return {"name": name, "returncode": proc.returncode, "ok": proc.returncode == 0 and bool(payload.get("ok", True)), "log": str(log), "payload": payload}


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    runs = [
        _run("packager_rc_smoke", [sys.executable, "-m", "linyuanzhe_frontend.run_packager_rc_smoke"], FRONTEND_PARENT),
        _run("startup_self_check_l669", [sys.executable, str(ROOT / "installer" / "startup" / "startup_self_check_l669.py")], ROOT),
        _run("version_slot_validation_l669", [sys.executable, str(ROOT / "installer" / "build" / "version_slot_validate_l669.py")], ROOT),
        _run("windows_packager_dry_run_l669", [sys.executable, str(ROOT / "installer" / "build" / "package_builder_dry_run_l669.py")], ROOT),
        _run("release_pipeline_preflight_l669", [sys.executable, str(ROOT / "installer" / "release" / "release_pipeline_preflight_l669.py")], ROOT),
    ]
    summary = {
        "contract_version": "tiangong.l6_69.package_builder_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": all(item["ok"] for item in runs),
        "runs": runs,
        "dry_run_only": True,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "frontend_built_installer": False,
        "runtime_core_mutation": False,
        "ready_for_combine": False,
        "merge_blockers": ["real Runtime instance smoke not executed"],
    }
    out = REPORTS / "package_builder_preflight_l669.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "ready_for_combine": False, "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
