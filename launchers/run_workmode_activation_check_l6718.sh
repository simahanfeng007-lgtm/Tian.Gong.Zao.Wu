#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend/project"
STATE_DIR="$(mktemp -d -t linyuanzhe_workmode_XXXXXX)"
trap 'rm -rf "$STATE_DIR"' EXIT
export LINYUANZHE_STATE_DIR="$STATE_DIR"
export TIANGONG_STATE_DIR="$STATE_DIR"
export TIANGONG_SOUL_BASELINE_PATH="$STATE_DIR/soul/soul_emotion_baseline.json"
export TIANGONG_PROMPT_TRACE_FILE="$STATE_DIR/prompt_trace/prompt_trace.jsonl"
export TIANGONG_PROMPT_TUNER_FILE="$STATE_DIR/prompt_trace/prompt_tuning_state.json"
export PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=. python -S -B run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate status"
PYTHONPATH=. python -S -B run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate smoke 工作模式确认"
PYTHONPATH=. python -S -B run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "runtime-tools align"
COMPILE_TARGETS=(tiangong_agent_runtime tiangong_agent_shell)
if [ -d .linyuanzhe/active_assets ]; then
  COMPILE_TARGETS+=(.linyuanzhe/active_assets)
fi
python -S -B run_no_pyc_compile_check_l6738.py "${COMPILE_TARGETS[@]}"
if [ -d tests ]; then
  PYTHONPATH=. pytest -q tests
else
  echo "SKIP: 净包不携带 pytest tests 目录；已完成 mock run_agent 与 no-pyc compile 验收。"
fi
