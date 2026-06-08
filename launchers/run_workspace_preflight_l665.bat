@echo off
chcp 65001 >nul
cd /d %~dp0..
python scripts\workspace_preflight_l665.py %*
