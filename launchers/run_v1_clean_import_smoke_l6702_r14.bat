@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0\..\backend\project"
python -S -B run_v1_clean_import_smoke.py
