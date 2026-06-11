@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
setlocal
set ROOT_DIR=%~dp0..\
python -S -B "%ROOT_DIR%scripts\file_transfer_interrupt_preflight_l664.py" %*
endlocal
