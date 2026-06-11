from __future__ import annotations

"""Compatibility shim for the historical launcher verifier name.

The implementation delegates to the current L6.73.8 verifier and current
launcher manifest, including executable-bit restoration and full wrapper checks.
"""

import runpy
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).with_name("verify_launchers_l67220.py")
    namespace = runpy.run_path(str(script))
    target_main = namespace.get("main")
    if not callable(target_main):
        print("current launcher verifier has no callable main()", file=sys.stderr)
        return 2
    return int(target_main())


if __name__ == "__main__":
    raise SystemExit(main())
