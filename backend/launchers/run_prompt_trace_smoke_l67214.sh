#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../project"
STATE_DIR="$(mktemp -d -t linyuanzhe_prompt_trace_XXXXXX)"
trap 'rm -rf "$STATE_DIR"' EXIT
export LINYUANZHE_STATE_DIR="$STATE_DIR"
export TIANGONG_STATE_DIR="$STATE_DIR"
export TIANGONG_SOUL_BASELINE_PATH="$STATE_DIR/soul/soul_emotion_baseline.json"
export TIANGONG_PROMPT_TRACE_FILE="$STATE_DIR/prompt_trace/prompt_trace.jsonl"
export TIANGONG_PROMPT_TUNER_FILE="$STATE_DIR/prompt_trace/prompt_tuning_state.json"
export PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=. python3 -S -B run_prompt_trace_smoke_l67214.py
