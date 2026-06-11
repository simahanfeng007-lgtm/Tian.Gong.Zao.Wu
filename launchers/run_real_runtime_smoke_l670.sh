export PYTHONDONTWRITEBYTECODE=1
#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 -S -B scripts/real_runtime_endpoint_smoke_l670.py --require-real
