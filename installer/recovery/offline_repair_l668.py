from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.68 offline repair dry-run helper")
    parser.add_argument("--apply", action="store_true", help="RC pre-stage blocks apply; this flag intentionally returns non-zero.")
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    if args.apply:
        payload = {
            "contract_version": "tiangong.l6_68.offline_repair.v1",
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "ok": False,
            "blocked": True,
            "reason": "apply is disabled in L6.68 RC pre-stage",
            "runtime_core_mutation": False,
        }
        out = REPORTS / "offline_repair_l668.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": False, "blocked": True, "report": str(out)}, ensure_ascii=False, indent=2))
        return 3
    manifest = ROOT / "installer" / "installer_manifest_l668.json"
    payload = {
        "contract_version": "tiangong.l6_68.offline_repair.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": manifest.exists(),
        "dry_run": True,
        "manifest_present": manifest.exists(),
        "suggested_actions": [
            "run startup self-check",
            "verify package sha256",
            "verify active and rollback slot manifests",
            "run RC preflight before launching desktop shell"
        ],
        "frontend_applied_fix": False,
        "runtime_core_mutation": False,
    }
    out = REPORTS / "offline_repair_l668.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
