#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
python -S -B run_learning_asset_contract_smoke.py
