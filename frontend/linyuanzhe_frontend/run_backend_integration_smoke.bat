@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
cd /d "%~dp0\.."
python -S -B -m linyuanzhe_frontend.run_backend_integration_smoke %*
