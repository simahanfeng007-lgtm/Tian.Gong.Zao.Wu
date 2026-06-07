from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"

REQUIRED_FILES = [
    "backend/project/run_agent.py",
    "frontend/linyuanzhe_frontend/app.py",
    "launchers/start_linyuanzhe_rc.py",
    "scripts/rc_preflight_l659.py",
    "scripts/real_runtime_unlock_l661.py",
    "scripts/scan_l659.py",
    "installer/installer_manifest_l668.json",
    "installer/installer_manifest_l669.json",
    "installer/build/build_plan_l669.json",
    "installer/build/version_slot_validate_l669.py",
    "installer/release/release_manifest_l669.json",
    "installer/signing/signing_policy_l669.json",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.69 Windows installer packager dry-run")
    parser.add_argument("--emit-installer", action="store_true", help="Disabled in L6.69; returns non-zero.")
    parser.add_argument("--out", default=str(REPORTS / "windows_packager_dry_run_l669.json"))
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    if args.emit_installer:
        payload = {
            "contract_version": "tiangong.l6_69.windows_packager_dry_run.v1",
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "ok": False,
            "blocked": True,
            "reason": "final installer artifact emission is disabled in L6.69 dry-run",
            "windows_installer_artifact_emitted": False,
            "runtime_core_mutation": False,
        }
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": False, "blocked": True, "report": str(out)}, ensure_ascii=False, indent=2))
        return 3

    file_checks = []
    digest_manifest = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        exists = path.exists()
        file_checks.append({"file": rel, "ok": exists})
        if exists and path.is_file():
            digest_manifest.append({"file": rel, "sha256": _file_digest(path)})
    build_plan = _read_json(ROOT / "installer" / "build" / "build_plan_l669.json")
    release_manifest = _read_json(ROOT / "installer" / "release" / "release_manifest_l669.json")
    signing_policy = _read_json(ROOT / "installer" / "signing" / "signing_policy_l669.json")
    checks = {
        "required_files_present": all(item["ok"] for item in file_checks),
        "build_plan_dry_run_only": build_plan.get("stage") == "dry_run_only" and "exe" in build_plan.get("blocked_outputs", []),
        "release_blocks_final_installer": release_manifest.get("final_installer_allowed") is False,
        "release_requires_real_runtime_unlock": release_manifest.get("real_runtime_unlock_required") is True,
        "signing_policy_has_no_key_material": signing_policy.get("signing_key_material_in_package") is False and signing_policy.get("certificate_path_in_package") is False,
        "no_windows_installer_emitted": True,
        "frontend_does_not_build_installer": True,
        "runtime_core_not_mutated": True,
    }
    ok = all(value is True for value in checks.values())
    payload = {
        "contract_version": "tiangong.l6_69.windows_packager_dry_run.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "dry_run": True,
        "checks": checks,
        "file_checks": file_checks,
        "digest_manifest": digest_manifest,
        "planned_artifacts": [
            {"name": "windows_installer_exe", "status": "not_emitted"},
            {"name": "windows_installer_msi", "status": "not_emitted"},
            {"name": "engineering_rc_zip", "status": "built_by_release_packaging_after_validation"},
        ],
        "windows_installer_artifact_emitted": False,
        "signing_key_material_loaded": False,
        "frontend_built_installer": False,
        "runtime_core_mutation": False,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
