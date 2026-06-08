#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CHECKER="$ROOT/00_ASCII_START_HERE/python/DEPENDENCY_CHECK.py"

echo "[天工造物 v2.0] 一键依赖检测"

PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$candidate" &>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo "[天工造物] 未找到 Python。请安装 Python 3.10+。"
  exit 1
fi

"$PYTHON" "$CHECKER"
exit $?
