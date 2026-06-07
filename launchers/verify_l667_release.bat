@echo off
cd /d "%~dp0\.."
python scripts\verify_l667_release.py %*
