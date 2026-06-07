#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "[临渊者] 启动 FE.01 桌面演示包..."
python3 run_desktop_demo.py
