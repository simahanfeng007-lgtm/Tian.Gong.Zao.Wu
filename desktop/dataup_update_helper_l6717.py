from __future__ import annotations

"""Desktop helper wrapper for DataUp safe update.

It delegates all logic to scripts/dataup_update_core_l6717.py so the Tk frontend
never copies files itself. Windows users may run this helper from a .bat entry
or let the Settings/System page launch it after confirmation.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "dataup_update_core_l6717.py"
DEFAULT_TIMEOUT_SECONDS = 900


def _timeout_seconds() -> int:
    raw = __import__("os").environ.get("LINYUANZHE_DATAUP_HELPER_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return min(max(value, 30), 3600)


def main() -> int:
    if not CORE.exists():
        print("DataUp core missing:", CORE)
        return 2
    cmd = [sys.executable, str(CORE), "--root", str(ROOT), *sys.argv[1:]]
    timeout = _timeout_seconds()
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"DataUp helper timeout after {timeout} seconds.", file=sys.stderr)
        return 124
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
