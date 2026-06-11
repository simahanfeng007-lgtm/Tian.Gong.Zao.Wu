@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0\..\backend\project"
python -S -B run_learning_asset_activation_smoke.py
