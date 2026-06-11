from __future__ import annotations

"""Validate a local DataUp package without applying it."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dataup_update_core_l6717 import plan_package, _plan_to_dict, _write_report, SCHEMA  # type: ignore


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Linyuanzhe DataUp package")
    parser.add_argument("--package", required=True)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    try:
        plan = plan_package(Path(args.package), root)
        payload = {"schema": SCHEMA + ".manifest_validate", "ok": plan.ok, "plan": _plan_to_dict(plan)}
    except Exception as exc:
        payload = {"schema": SCHEMA + ".manifest_validate", "ok": False, "error": str(exc)[:1000]}
    out = _write_report(root, "dataup_manifest_validate_l6717.json", payload, Path(args.report).resolve() if args.report else None)
    payload["report"] = str(out)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
