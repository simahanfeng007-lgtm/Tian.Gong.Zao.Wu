from __future__ import annotations

"""Compatibility shim for the historical launcher generator name.

The implementation intentionally delegates to the current L6.73.8 generator so
the legacy filename cannot regenerate stale launcher text or version identity.
"""

import runpy
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).with_name("generate_launchers_l67220.py")
    namespace = runpy.run_path(str(script))
    target_main = namespace.get("main")
    if not callable(target_main):
        print("current launcher generator has no callable main()", file=sys.stderr)
        return 2
    return int(target_main())


if __name__ == "__main__":
    raise SystemExit(main())
