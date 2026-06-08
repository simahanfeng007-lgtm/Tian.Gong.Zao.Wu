from __future__ import annotations

import sys
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
DESKTOP = ROOT / "desktop"
sys.path.insert(0, str(DESKTOP))
sys.argv = [sys.argv[0], "--self-check", *sys.argv[1:]]
runpy.run_path(str(DESKTOP / "start_linyuanzhe_desktop_l671.py"), run_name="__main__")
