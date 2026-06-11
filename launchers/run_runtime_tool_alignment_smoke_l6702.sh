#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../backend/project"
PYTHONPATH=. python -S -B run_runtime_tool_alignment_smoke.py
