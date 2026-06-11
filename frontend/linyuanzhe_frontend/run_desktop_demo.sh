#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "[临渊者] 旧 Mock 演示入口已废弃，转到兼容提示..."
PYTHON_BIN="${PYTHON_BIN:-python3}"
case "$PYTHON_BIN" in
  python|python3|python3.[0-9]|python3.[0-9][0-9]|/*/python|/*/python3|/*/python3.[0-9]|/*/python3.[0-9][0-9]) ;;
  *) echo "[临渊者] PYTHON_BIN 不被允许: $PYTHON_BIN" >&2; exit 23 ;;
esac
PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" -S -B run_desktop_demo.py
