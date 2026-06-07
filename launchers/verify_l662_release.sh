#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/backend/project:$ROOT/frontend${PYTHONPATH:+:$PYTHONPATH}"
python3 "$ROOT/scripts/verify_l662_release.py" "$@"
