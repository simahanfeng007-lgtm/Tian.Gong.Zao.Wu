#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend/project"
PYTHONPATH=. python3 run_learning_asset_sandbox_alignment_smoke.py
