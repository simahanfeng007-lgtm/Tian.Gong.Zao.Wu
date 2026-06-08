#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "[临渊者] 验证 FE.01 STEP15 / L6.54 顺滑层包..."
python3 scripts/validate_demo_package.py
