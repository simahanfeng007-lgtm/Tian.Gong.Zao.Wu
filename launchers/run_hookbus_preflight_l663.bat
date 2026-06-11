@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
setlocal
set "ROOT_DIR=%~dp0.."
python -S -B "%ROOT_DIR%\scripts\hookbus_preflight_l663.py" %*
exit /b %ERRORLEVEL%
