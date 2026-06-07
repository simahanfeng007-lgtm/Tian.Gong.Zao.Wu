@echo off
setlocal
set ROOT=%~dp0..
set PYTHONPATH=%ROOT%\backend\project;%ROOT%\frontend;%PYTHONPATH%
python "%ROOT%\scripts\observability_preflight_l662.py" %*
endlocal
