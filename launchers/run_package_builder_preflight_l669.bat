@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python scripts\package_builder_preflight_l669.py
