@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0..\backend\project"
set PYTHONPATH=.
python run_learning_asset_sandbox_alignment_smoke.py
endlocal
