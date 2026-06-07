#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/installer_rc_preflight_l668.py "$@"
