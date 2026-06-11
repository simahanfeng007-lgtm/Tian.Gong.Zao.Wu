@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0..\backend\project"
python -S -B "run_dataup_signature_guard_smoke_l67217.py"
exit /b %ERRORLEVEL%
