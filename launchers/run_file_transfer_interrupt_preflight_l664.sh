#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -S -B "$ROOT_DIR/scripts/file_transfer_interrupt_preflight_l664.py" "$@"
