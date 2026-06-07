@echo off
setlocal
set "ROOT_DIR=%~dp0.."
python "%ROOT_DIR%\scripts\hookbus_preflight_l663.py" %*
exit /b %ERRORLEVEL%
