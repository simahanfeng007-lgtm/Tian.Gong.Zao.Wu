@echo off
chcp 65001 >nul
cd /d %~dp0\..\backend\project
set PYTHONPATH=.
python run_learning_asset_release_gate_smoke.py
