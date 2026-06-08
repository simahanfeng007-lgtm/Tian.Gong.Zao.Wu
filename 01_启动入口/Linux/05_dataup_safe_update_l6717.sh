#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 "desktop/dataup_update_helper_l6717.py" --source auto --apply --yes
