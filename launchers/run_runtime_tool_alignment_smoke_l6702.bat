@echo off
chcp 65001 >nul
cd /d "%~dp0..\backend\project"
set PYTHONPATH=.
python run_runtime_tool_alignment_smoke.py
