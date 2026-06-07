#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/real_runtime_gate_l660.py --require-real "$@"
