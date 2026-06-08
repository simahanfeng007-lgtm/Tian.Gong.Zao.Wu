#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend/project"
PYTHONPATH=. python run_runtime_tool_alignment_smoke.py
