@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0\.."
python -S -B -m linyuanzhe_frontend.scripts.validate_demo_package %*
