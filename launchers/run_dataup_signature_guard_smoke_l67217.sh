#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
python3 -S -B run_dataup_signature_guard_smoke_l67217.py
