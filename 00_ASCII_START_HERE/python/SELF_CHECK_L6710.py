from __future__ import annotations

"""Cross-platform categorized self-check entry for FE01 STEP31J / L6.71.0."""

import runpy
from pathlib import Path
import sys


def find_project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (
            (candidate / "desktop" / "start_linyuanzhe_desktop_l671.py").exists()
            and (candidate / "frontend" / "linyuanzhe_frontend" / "app.py").exists()
            and (candidate / "backend" / "project").exists()
        ):
            return candidate
    raise SystemExit("未找到临渊者桌面端项目根目录：请保持 01_启动入口、desktop、frontend、backend 在同一包内。")


ROOT = find_project_root()
DESKTOP = ROOT / "desktop"
sys.path.insert(0, str(DESKTOP))
sys.argv = [sys.argv[0], "--self-check", *sys.argv[1:]]
runpy.run_path(str(DESKTOP / "start_linyuanzhe_desktop_l671.py"), run_name="__main__")
