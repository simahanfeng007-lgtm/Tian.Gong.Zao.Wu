from __future__ import annotations

import sys
from pathlib import Path

_ASCII_PY = Path(__file__).resolve().parents[2] / "00_ASCII_START_HERE" / "python"
if str(_ASCII_PY) not in sys.path:
    sys.path.insert(0, str(_ASCII_PY))

from _entry_common_l67217 import main_start_desktop


if __name__ == "__main__":
    raise SystemExit(main_start_desktop(anchor=Path(__file__)))
