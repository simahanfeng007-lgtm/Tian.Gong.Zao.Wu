@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
python scripts\verify_l667_release.py %*
