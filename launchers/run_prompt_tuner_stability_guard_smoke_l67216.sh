#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/backend/project"
PYTHONPATH=. python -S -B run_prompt_tuner_stability_guard_smoke_l67216.py
