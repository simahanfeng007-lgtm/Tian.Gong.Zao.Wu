from __future__ import annotations

"""Compatibility shim for the old L6.71.0 launcher layout audit.

Current builds use ``launcher_manifest_l67220.json`` and a generated launcher
verifier. The historical hard-coded L6710 file list drifted from the current
manifest and produced false release blockers. Keep this script as a stable CI
entry, but validate the active manifest instead of obsolete launcher names.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts" / "verify_launchers_l67220.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location("verify_launchers_l67220", VERIFY_PATH)
    if spec is None or spec.loader is None:
        print(f"FAIL: cannot load {VERIFY_PATH.relative_to(ROOT)}", file=sys.stderr)
        return 1
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows, errors = module.verify(ROOT)
    for row in rows:
        print(row)
    if errors:
        print("[desktop_entry_layout_audit_l6710] delegated launcher verification FAILED", file=sys.stderr)
        for error in errors:
            print("FAIL  " + error, file=sys.stderr)
        return 1
    print(f"PASS: delegated to launcher_manifest_l67220 verifier; entries={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
