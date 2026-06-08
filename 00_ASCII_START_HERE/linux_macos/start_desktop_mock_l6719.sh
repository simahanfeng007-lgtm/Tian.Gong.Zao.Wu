#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

# 依赖检测
CHECKER="$ROOT/00_ASCII_START_HERE/python/DEPENDENCY_CHECK.py"
PYTHON=""
for c in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" &>/dev/null && "$c" -c "import tkinter" 2>/dev/null; then
    PYTHON="$c"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "[天工造物] 未找到可用的 Python 3 + tkinter。请安装 Python 3.10+。"
  exit 1
fi
echo "[天工造物 v2.0] 正在检测 Python 环境..."
"$PYTHON" "$CHECKER" || exit 1
echo "依赖检测通过，正在启动..."
"$PYTHON" "00_ASCII_START_HERE/python/START_DESKTOP_L6710.py" --backend-mode mock "$@"
