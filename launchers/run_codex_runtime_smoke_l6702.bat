@echo off
chcp 65001 >nul
set ROOT=%~dp0\..
cd /d "%ROOT%\backend\project"
python run_codex_runtime_smoke.py
