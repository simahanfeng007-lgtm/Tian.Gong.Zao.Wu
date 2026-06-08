#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend/project"
PYTHONPATH=. python run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate status"
PYTHONPATH=. python run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate smoke 工作模式确认"
PYTHONPATH=. python run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "runtime-tools align"
python -m compileall -q tiangong_agent_runtime tiangong_agent_shell .linyuanzhe/active_assets tests
PYTHONPATH=. pytest -q
