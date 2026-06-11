#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
python3 -S -B scripts/real_runtime_gate_l660.py --require-real "$@"
