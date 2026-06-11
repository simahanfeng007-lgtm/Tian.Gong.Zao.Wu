@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0..\backend\project"
set PYTHONPATH=.
python -S -B run_runtime_tool_alignment_smoke.py
