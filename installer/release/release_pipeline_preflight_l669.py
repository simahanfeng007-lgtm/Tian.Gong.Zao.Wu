from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_l669_reports_"))


def _run(name: str, cmd: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["LINYUANZHE_REPORT_DIR"] = str(REPORTS)
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=120)
    log = REPORTS / f"l669_{name}.log"
    log.write_text((proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    payload: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"parse_error": "stdout was not json"}
    return {"name": name, "returncode": proc.returncode, "ok": proc.returncode == 0 and bool(payload.get("ok", True)), "log": log.name, "payload": payload}


def _load_json(rel: str) -> dict[str, Any]:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    release_manifest = _load_json("installer/release/release_manifest_l669.json")
    signing_policy = _load_json("installer/signing/signing_policy_l669.json")
    runs = [
        _run("startup_self_check_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "startup" / "startup_self_check_l669.py")]),
        _run("version_slot_validation_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "build" / "version_slot_validate_l669.py")]),
        _run("windows_packager_dry_run_l669", [sys.executable, "-S", "-B", str(ROOT / "installer" / "build" / "package_builder_dry_run_l669.py"), "--out", str(REPORTS / "windows_packager_dry_run_l669.json")]),
    ]
    manifest_checks = {
        "release_contract_ok": release_manifest.get("contract_version") == "tiangong.l6_69.release_manifest.v1",
        "identity_preserved": release_manifest.get("unique_developer") == "于泳翔" and release_manifest.get("angel_investor") == "胖胖龙",
        "final_installer_disabled": release_manifest.get("final_installer_allowed") is False,
        "real_runtime_unlock_required": release_manifest.get("real_runtime_unlock_required") is True,
        "signing_required_for_final": release_manifest.get("signing_required_for_final") is True,
        "no_signing_secret_in_package": signing_policy.get("signing_key_material_in_package") is False,
        "no_certificate_path_in_package": signing_policy.get("certificate_path_in_package") is False,
    }
    ok = all(item["ok"] for item in runs) and all(manifest_checks.values())
    payload = {
        "contract_version": "tiangong.l6_69.release_pipeline_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "manifest_checks": manifest_checks,
        "runs": runs,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "ready_for_combine": False,
        "merge_blockers": ["real Runtime instance smoke not executed"],
        "runtime_core_mutation": False,
    }
    out = REPORTS / "release_pipeline_preflight_l669.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "ready_for_combine": False, "report": out.name}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
