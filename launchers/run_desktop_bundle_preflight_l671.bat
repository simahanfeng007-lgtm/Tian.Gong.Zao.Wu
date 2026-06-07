@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
python scripts\desktop_bundle_preflight_l671.py
