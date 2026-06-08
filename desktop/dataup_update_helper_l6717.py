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


def main() -> int:
    if not CORE.exists():
        print("DataUp core missing:", CORE)
        return 2
    cmd = [sys.executable, str(CORE), "--root", str(ROOT), *sys.argv[1:]]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
