@echo off
chcp 65001 >nul
cd /d %~dp0\..\backend\project
python run_v1_clean_import_smoke.py
