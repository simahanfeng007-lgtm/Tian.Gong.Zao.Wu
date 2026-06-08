from __future__ import annotations

"""Cross-platform root launcher for 临渊者 desktop FE01 STEP31I / L6.70.9."""

import runpy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
DESKTOP = ROOT / "desktop"
sys.path.insert(0, str(DESKTOP))
runpy.run_path(str(DESKTOP / "start_linyuanzhe_desktop_l671.py"), run_name="__main__")
