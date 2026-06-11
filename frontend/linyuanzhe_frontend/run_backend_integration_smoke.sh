#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
python -S -B -m linyuanzhe_frontend.run_backend_integration_smoke "$@"
