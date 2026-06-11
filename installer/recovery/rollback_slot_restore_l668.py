from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(description="L6.68 rollback slot restore plan generator")
    parser.add_argument("--apply", action="store_true", help="RC pre-stage blocks apply; only a plan may be generated.")
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    blocked = bool(args.apply)
    payload = {
        "contract_version": "tiangong.l6_68.rollback_plan.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": not blocked,
        "blocked": blocked,
        "reason": "rollback apply is disabled in L6.68 RC pre-stage" if blocked else "plan generated",
        "plan": [
            "verify rollback slot manifest",
            "verify package digest",
            "stop desktop shell through Runtime control path",
            "switch active slot through installer controller",
            "run startup self-check after restore"
        ],
        "frontend_applied_rollback": False,
        "runtime_core_mutation": False,
    }
    out = REPORTS / "rollback_plan_l668.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "blocked": blocked, "report": str(out)}, ensure_ascii=False, indent=2))
    return 3 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
