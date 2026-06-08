@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
python scripts\session_manager_preflight_l667.py %*
