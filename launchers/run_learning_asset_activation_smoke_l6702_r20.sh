#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend/project"
python run_learning_asset_activation_smoke.py
