#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/workspace_preflight_l665.py "$@"
