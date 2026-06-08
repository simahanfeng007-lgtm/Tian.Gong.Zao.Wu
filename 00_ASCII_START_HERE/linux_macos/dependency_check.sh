#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CHECKER="$ROOT/00_ASCII_START_HERE/python/DEPENDENCY_CHECK.py"

echo "[Tiangong v2.0] Dependency check"

PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$candidate" &>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo "[Tiangong] Python not found. Install Python 3.10+."
  exit 1
fi

"$PYTHON" "$CHECKER"
exit $?
