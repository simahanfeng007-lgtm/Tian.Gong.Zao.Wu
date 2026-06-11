from __future__ import annotations

"""Restore executable bits for POSIX launchers after Python zipfile extraction.

Python's ``zipfile.extractall`` does not restore UNIX executable mode on some
platforms. This helper is safe and local-only: it only chmods bundled ``.sh``
and ``.command`` files under the extracted package root.
"""

import os
import stat
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = project_root()
    count = 0
    for pattern in ("*.sh", "*.command"):
        for path in root.rglob(pattern):
            if not path.is_file():
                continue
            try:
                mode = path.stat().st_mode
                if not (mode & stat.S_IXUSR):
                    os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    count += 1
            except OSError as exc:
                print(f"restore_posix_executable_bits FAIL: {path.relative_to(root)}: {exc}", file=sys.stderr)
                return 1
    print(f"restore_posix_executable_bits PASS: restored {count} POSIX script executable bits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
