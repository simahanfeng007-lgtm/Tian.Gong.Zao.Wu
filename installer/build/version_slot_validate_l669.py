from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_l669_reports_"))
SLOTS = ROOT / "installer" / "version_slots"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    expected = {
        "active": SLOTS / "active" / "slot_manifest_l669.json",
        "rollback": SLOTS / "rollback" / "slot_manifest_l669.json",
        "candidate": SLOTS / "candidate" / "slot_manifest_l669.json",
    }
    checks: list[dict[str, Any]] = []
    slot_payloads: dict[str, dict[str, Any]] = {}
    for name, path in expected.items():
        exists = path.exists()
        payload: dict[str, Any] = {}
        if exists:
            try:
                payload = _load_json(path)
            except json.JSONDecodeError as exc:
                payload = {"error": str(exc)[:160]}
        state_ok = bool(payload.get("slot_name") == name and payload.get("state") in {"active", "rollback", "candidate", "standby"})
        checks.append({"check_id": f"slot_{name}", "ok": exists and state_ok, "path": str(path.relative_to(ROOT)), "state": payload.get("state", "missing")})
        slot_payloads[name] = payload
    active_ok = slot_payloads.get("active", {}).get("rollback_capable") is True
    rollback_ok = slot_payloads.get("rollback", {}).get("rollback_capable") is True
    candidate_ok = slot_payloads.get("candidate", {}).get("rollback_capable") is False and slot_payloads.get("candidate", {}).get("package_sha256_digest") == "dry-run-no-binary"
    checks.extend([
        {"check_id": "active_rollback_capable", "ok": active_ok},
        {"check_id": "rollback_ready", "ok": rollback_ok},
        {"check_id": "candidate_is_dry_run_only", "ok": candidate_ok},
    ])
    ok = all(item.get("ok") for item in checks)
    payload = {
        "contract_version": "tiangong.l6_69.version_slot_validation.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "checks": checks,
        "slot_summary": {name: {"state": data.get("state"), "version_label": data.get("version_label"), "path_digest": data.get("path_digest")} for name, data in slot_payloads.items()},
        "slot_mutation_performed": False,
        "frontend_applied_rollback": False,
        "runtime_core_mutation": False,
    }
    out = REPORTS / "version_slot_validation_l669.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "report": out.name}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
