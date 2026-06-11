#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
python -S -B scripts/session_manager_preflight_l667.py "$@"
