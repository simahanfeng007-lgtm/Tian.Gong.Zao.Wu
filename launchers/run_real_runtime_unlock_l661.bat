@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
setlocal
set ROOT=%~dp0..
python -S -B "%ROOT%\scripts\real_runtime_unlock_l661.py" --require-real %*
exit /b %ERRORLEVEL%
