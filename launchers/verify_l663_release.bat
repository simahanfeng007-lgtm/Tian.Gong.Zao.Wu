@echo off
chcp 65001 >nul
setlocal
set "ROOT_DIR=%~dp0.."
python "%ROOT_DIR%\scripts\verify_l663_release.py" %*
exit /b %ERRORLEVEL%
