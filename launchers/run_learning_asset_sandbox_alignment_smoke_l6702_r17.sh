#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
PYTHONPATH=. python3 -S -B run_learning_asset_sandbox_alignment_smoke.py
