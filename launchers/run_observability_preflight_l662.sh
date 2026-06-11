#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/backend/project:$ROOT/frontend${PYTHONPATH:+:$PYTHONPATH}"
python3 -S -B "$ROOT/scripts/observability_preflight_l662.py" "$@"
