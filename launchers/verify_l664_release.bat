@echo off
chcp 65001 >nul
setlocal
set ROOT_DIR=%~dp0..\
python "%ROOT_DIR%scripts\verify_l664_release.py" %*
endlocal
