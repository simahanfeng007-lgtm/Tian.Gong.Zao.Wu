#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m linyuanzhe_frontend.run_backend_integration_smoke "$@"
