@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
setlocal
cd /d "%~dp0..\backend\project"
set "PYTHONPATH=."
python -S -B run_active_assets_relocation_smoke_l67211.py
if errorlevel 1 (
  echo L6721.1 active assets relocation smoke failed.
  pause
  exit /b 1
)
echo L6721.1 active assets relocation smoke passed.
pause
