from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from linyuanzhe_frontend.app import main


if __name__ == "__main__":
    runtime_url = os.environ.get("LINYUANZHE_RUNTIME_URL", "http://127.0.0.1:8787")
    raise SystemExit(main(["--runtime-url", runtime_url]))
