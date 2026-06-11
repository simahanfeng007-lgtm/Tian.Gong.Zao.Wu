#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -S -B -m linyuanzhe_frontend.run_rc_preflight "$@"
