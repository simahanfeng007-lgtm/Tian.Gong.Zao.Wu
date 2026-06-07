#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "启动临渊者桌面端：前端 + 本地桥接后端"
python3 desktop/start_linyuanzhe_desktop_l671.py --backend-mode mock
