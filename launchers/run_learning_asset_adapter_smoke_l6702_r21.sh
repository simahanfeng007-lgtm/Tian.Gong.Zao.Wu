#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend/project"
export PYTHONDONTWRITEBYTECODE=1
python -S -B -S run_learning_asset_adapter_smoke.py
