@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
set ROOT=%~dp0\..
cd /d "%ROOT%\backend\project"
python -S -B run_codex_runtime_smoke.py
