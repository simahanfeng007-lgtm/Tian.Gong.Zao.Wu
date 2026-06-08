#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend/project"
PYTHONPATH=. python3 run_learning_asset_release_gate_smoke.py
