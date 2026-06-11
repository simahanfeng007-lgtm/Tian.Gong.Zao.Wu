#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
python3 -S -B run_v1_clean_import_smoke.py
