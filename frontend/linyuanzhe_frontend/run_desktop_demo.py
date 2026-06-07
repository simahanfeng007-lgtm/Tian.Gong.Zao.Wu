from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from linyuanzhe_frontend.app import main


if __name__ == "__main__":
    mock_file = ROOT / "mock_data" / "runtime_snapshot_mock.json"
    raise SystemExit(main(["--mock-file", str(mock_file)]))
