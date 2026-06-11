#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../project"
python3 -S -B run_homeostasis_prompt_tuner_smoke_l67215.py
