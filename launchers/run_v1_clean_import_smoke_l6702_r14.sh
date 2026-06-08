#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend/project"
python3 run_v1_clean_import_smoke.py
