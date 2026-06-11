@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
set ROOT=%~dp0\..
cd /d "%ROOT%\frontend\linyuanzhe_frontend"
python -S -B run_codex_bridge_smoke.py
