#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 launchers/start_linyuanzhe_rc.py "$@"
