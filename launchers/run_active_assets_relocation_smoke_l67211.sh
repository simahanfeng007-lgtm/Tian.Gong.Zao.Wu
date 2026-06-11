#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
PYTHONPATH=. python -S -B run_active_assets_relocation_smoke_l67211.py
