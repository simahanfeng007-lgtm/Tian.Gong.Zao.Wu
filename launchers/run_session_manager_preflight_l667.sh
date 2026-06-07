#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/session_manager_preflight_l667.py "$@"
