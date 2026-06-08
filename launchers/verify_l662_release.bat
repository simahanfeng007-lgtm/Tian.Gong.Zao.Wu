@echo off
chcp 65001 >nul
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\backend\project;%ROOT%\frontend;%PYTHONPATH%
python "%ROOT%\scripts\verify_l662_release.py" %*
endlocal
