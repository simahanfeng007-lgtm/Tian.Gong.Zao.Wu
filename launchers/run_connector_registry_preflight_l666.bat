@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0.."
python -S -B scripts\connector_registry_preflight_l666.py %*
