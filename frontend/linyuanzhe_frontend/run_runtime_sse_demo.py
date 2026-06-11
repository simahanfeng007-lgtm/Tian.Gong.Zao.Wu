from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

def _headless_display_unavailable() -> bool:
    if os.name == "nt":
        return False
    return not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


if __name__ == "__main__" and os.environ.get("TIANGONG_RUN_GUI_DEMO_FULL") != "1":
    reason = "headless or demo launch disabled by default"
    print(f"runtime_sse_demo SKIP: {reason}; set TIANGONG_RUN_GUI_DEMO_FULL=1 to launch the GUI demo.")
    raise SystemExit(0)


from linyuanzhe_frontend.app import main


if __name__ == "__main__":
    runtime_url = os.environ.get("LINYUANZHE_RUNTIME_URL", "http://127.0.0.1:8787")
    raise SystemExit(main(["--runtime-url", runtime_url]))
