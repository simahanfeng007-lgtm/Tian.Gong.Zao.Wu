@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0.."
python -S -B scripts\workspace_preflight_l665.py %*
