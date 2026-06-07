#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 scripts/real_runtime_endpoint_smoke_l670.py --require-real
