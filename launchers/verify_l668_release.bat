@echo off
cd /d "%~dp0\.."
python scripts\verify_l668_release.py %*
