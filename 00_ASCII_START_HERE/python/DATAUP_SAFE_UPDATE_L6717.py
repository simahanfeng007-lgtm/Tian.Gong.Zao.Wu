from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "desktop" / "dataup_update_helper_l6717.py"

if __name__ == "__main__":
    raise SystemExit(subprocess.run([sys.executable, str(HELPER), "--source", "auto", "--apply", "--yes"], cwd=str(ROOT)).returncode)
