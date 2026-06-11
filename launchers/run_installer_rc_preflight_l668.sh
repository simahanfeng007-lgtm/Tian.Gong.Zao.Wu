#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
python -S -B scripts/installer_rc_preflight_l668.py "$@"
