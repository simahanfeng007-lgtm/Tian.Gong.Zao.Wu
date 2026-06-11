@echo off
set "PYTHONDONTWRITEBYTECODE=1"
setlocal
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
cd /d "%ROOT_DIR%\backend\project"
python -S -B run_organ_signal_card_smoke_l67212.py
exit /b %ERRORLEVEL%
