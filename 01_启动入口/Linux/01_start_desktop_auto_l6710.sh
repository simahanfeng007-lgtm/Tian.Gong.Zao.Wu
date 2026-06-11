#!/usr/bin/env bash
# GENERATED_BY=L6.73.8 LauncherTemplateGenerator
# ENTRY_KIND=start_desktop_auto
# TEMPLATE=posix_entry.template.sh
if [[ -z "${BASH_VERSION:-}" ]]; then
  echo "[Linyuanzhe] Bash is required." >&2
  exit 11
fi
if (( ${BASH_VERSINFO[0]:-0} < 3 )); then
  echo "[Linyuanzhe] Bash 3.0+ is required. Current: ${BASH_VERSION:-unknown}" >&2
  exit 12
fi
set -euo pipefail
shopt -s nullglob 2>/dev/null || true
SCRIPT_VERSION="L6.73.8"
TITLE="FE01 STEP68 / L6.73.8 - AUTO"
ENTRY_KIND="start_desktop_auto"
PY_ENTRY="00_ASCII_START_HERE/python/START_DESKTOP_L6710.py"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_DIR="$(pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ROOT=""

validate_python_bin() {
  case "$PYTHON_BIN" in
    python|python3|python3.[0-9]*|/*) ;;
    *)
      echo "[Linyuanzhe] Invalid PYTHON_BIN: $PYTHON_BIN" >&2
      echo "[Linyuanzhe] Allowed: python, python3, python3.x, or an absolute local path." >&2
      exit 31
      ;;
  esac
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "[Linyuanzhe] Python is not available: $PYTHON_BIN" >&2
    exit 32
  fi
}

looks_like_root() {
  local c="$1"
  [[ -f "$c/desktop/start_linyuanzhe_desktop_l671.py" && -f "$c/frontend/linyuanzhe_frontend/app.py" && -f "$c/backend/project/run_agent.py" && -f "$c/00_ASCII_START_HERE/python/START_DESKTOP_L6710.py" ]]
}

walk_up() {
  local c p i
  c="$(cd "$1" 2>/dev/null && pwd || true)"
  [[ -z "$c" ]] && return 1
  for i in {1..20}; do
    if looks_like_root "$c"; then ROOT="$c"; return 0; fi
    p="$(dirname "$c")"
    [[ "$p" == "$c" ]] && return 1
    c="$p"
  done
  return 1
}

scan_common() {
  local b="$1"
  [[ -n "$b" && -d "$b" ]] || return 1
  walk_up "$b" && return 0
  local d e f g
  for d in "$b"/*/; do
    [[ -d "$d" ]] || continue
    if looks_like_root "${d%/}"; then ROOT="${d%/}"; return 0; fi
  done
  for d in "$b"/*/; do
    for e in "$d"*/; do
      [[ -d "$e" ]] || continue
      if looks_like_root "${e%/}"; then ROOT="${e%/}"; return 0; fi
    done
  done
  for d in "$b"/*/; do
    for e in "$d"*/; do
      for f in "$e"*/; do
        [[ -d "$f" ]] || continue
        if looks_like_root "${f%/}"; then ROOT="${f%/}"; return 0; fi
      done
    done
  done
  for d in "$b"/*/; do
    for e in "$d"*/; do
      for f in "$e"*/; do
        for g in "$f"*/; do
          [[ -d "$g" ]] || continue
          if looks_like_root "${g%/}"; then ROOT="${g%/}"; return 0; fi
        done
      done
    done
  done
  return 1
}

validate_python_bin
walk_up "$SCRIPT_DIR" || walk_up "$START_DIR" || scan_common "$SCRIPT_DIR" || scan_common "$START_DIR" || scan_common "${HOME:-}/Desktop" || scan_common "${HOME:-}/Downloads" || scan_common "${HOME:-}/Documents" || true
if [[ -z "$ROOT" ]]; then
  echo "[Linyuanzhe] Project root not found."
  echo "[Linyuanzhe] Fully extract the ZIP first. Keep desktop, frontend, backend and 00_ASCII_START_HERE together."
  echo "[Linyuanzhe] If the path is too deep, move the package to Desktop or Downloads and retry."
  exit 20
fi
if [[ ! -f "$ROOT/$PY_ENTRY" ]]; then
  echo "[Linyuanzhe] Entry file missing: $ROOT/$PY_ENTRY" >&2
  exit 21
fi
export LINYUANZHE_ROOT_HINT="$ROOT"
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"
echo "[Linyuanzhe] $TITLE"
echo "[Linyuanzhe] Root: <package-root>"
# Local-only launcher. No remote download or remote HTTP execution is performed here.
exec "$PYTHON_BIN" -S -B "$ROOT/$PY_ENTRY" --backend-mode auto
