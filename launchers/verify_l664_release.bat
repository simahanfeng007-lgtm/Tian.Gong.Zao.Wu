@echo off
setlocal
set ROOT_DIR=%~dp0..\
python "%ROOT_DIR%scripts\verify_l664_release.py" %*
endlocal
