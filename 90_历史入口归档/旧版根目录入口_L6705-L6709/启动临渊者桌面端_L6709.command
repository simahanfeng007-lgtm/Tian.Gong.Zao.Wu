#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
exec "$PYTHON_BIN" START_DESKTOP_L6709.py --backend-mode auto "$@"
