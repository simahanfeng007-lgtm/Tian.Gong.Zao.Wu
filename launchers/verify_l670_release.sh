export PYTHONDONTWRITEBYTECODE=1
#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 -S -B scripts/verify_l670_release.py
