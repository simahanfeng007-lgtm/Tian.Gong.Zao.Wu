@echo off
chcp 65001 >nul
set ROOT=%~dp0\..
cd /d "%ROOT%\frontend\linyuanzhe_frontend"
python run_codex_bridge_smoke.py
