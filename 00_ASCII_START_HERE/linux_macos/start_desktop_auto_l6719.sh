#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

# Dependency check
CHECKER="$ROOT/00_ASCII_START_HERE/python/DEPENDENCY_CHECK.py"
PYTHON=""
for c in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" &>/dev/null && "$c" -c "import tkinter" 2>/dev/null; then
    PYTHON="$c"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "[Tiangong] Python 3 + tkinter not found. Install Python 3.10+."
  exit 1
fi
echo "[Tiangong v2.0] Checking Python environment..."
"$PYTHON" "$CHECKER" || exit 1
echo "Dependency check passed. Launching..."
"$PYTHON" "00_ASCII_START_HERE/python/START_DESKTOP_L6710.py" --backend-mode auto "$@"
