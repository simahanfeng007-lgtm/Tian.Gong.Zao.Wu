#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
python3 -S -B launchers/start_linyuanzhe_rc.py "$@"
