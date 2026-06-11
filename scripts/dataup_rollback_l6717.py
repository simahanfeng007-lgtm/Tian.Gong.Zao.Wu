from __future__ import annotations

"""Rollback helper for DataUp safe updater."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dataup_update_core_l6717 import rollback, _write_report, SCHEMA  # type: ignore


def _latest_backup(root: Path) -> Path:
    base = root / "backups"
    candidates = sorted(base.glob("dataup_rollback_*")) if base.exists() else []
    if not candidates:
        raise RuntimeError("no dataup rollback point found")
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback Linyuanzhe DataUp update")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--backup", default="")
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    try:
        backup = Path(args.backup).expanduser().resolve() if args.backup else _latest_backup(root)
        result = rollback(root, backup)
        payload = {"schema": SCHEMA + ".rollback", **result}
    except Exception as exc:
        payload = {"schema": SCHEMA + ".rollback", "ok": False, "error": str(exc)[:1000]}
    out = _write_report(root, "dataup_rollback_l6717.json", payload, Path(args.report).resolve() if args.report else None)
    payload["report"] = str(out)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
