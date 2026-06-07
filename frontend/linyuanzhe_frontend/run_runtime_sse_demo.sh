#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${LINYUANZHE_RUNTIME_URL:=http://127.0.0.1:8787}"
echo "[临渊者] 启动 FE.01 STEP13 Runtime SSE 接线模式：${LINYUANZHE_RUNTIME_URL}"
python3 run_runtime_sse_demo.py
