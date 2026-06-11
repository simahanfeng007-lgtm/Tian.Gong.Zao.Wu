#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python -S -B "$ROOT/scripts/real_runtime_unlock_l661.py" --require-real "$@"
