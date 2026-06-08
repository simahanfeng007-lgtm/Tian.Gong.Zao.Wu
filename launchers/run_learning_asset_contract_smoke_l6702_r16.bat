@echo off
chcp 65001 >nul
cd /d "%~dp0..\backend\project"
python run_learning_asset_contract_smoke.py
