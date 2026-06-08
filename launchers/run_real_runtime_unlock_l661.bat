@echo off
chcp 65001 >nul
setlocal
set ROOT=%~dp0..
python "%ROOT%\scripts\real_runtime_unlock_l661.py" --require-real %*
exit /b %ERRORLEVEL%
