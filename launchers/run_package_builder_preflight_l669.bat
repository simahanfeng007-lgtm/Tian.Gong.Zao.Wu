@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0.."
python -S -B scripts\package_builder_preflight_l669.py
