@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0.."
python -S -B scripts\real_runtime_gate_l660.py --require-real %*
