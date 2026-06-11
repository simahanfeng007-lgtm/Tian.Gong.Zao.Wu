@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0\..\backend\project"
set "PYTHONDONTWRITEBYTECODE=1"
python -S -B -S run_learning_asset_adapter_smoke.py
