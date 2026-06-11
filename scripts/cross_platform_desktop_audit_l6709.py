from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts" / "cross_platform_desktop_audit_l6710.py"), run_name="__main__")
