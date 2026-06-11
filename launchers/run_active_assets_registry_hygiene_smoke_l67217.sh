#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
python3 -S -B run_active_assets_registry_hygiene_smoke_l67217.py
