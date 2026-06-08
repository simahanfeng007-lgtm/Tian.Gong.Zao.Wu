#!/usr/bin/env sh
set -eu
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT"
echo "临渊者桌面端 FE01 STEP31J / L6.71.0 - 演示 Mock"
exec "$PYTHON_BIN" "$ROOT/01_启动入口/通用Python/START_DESKTOP_L6710.py" --backend-mode mock "$@"
