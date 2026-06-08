@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
python scripts\installer_rc_preflight_l668.py %*
