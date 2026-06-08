@echo off
chcp 65001 >nul
cd /d %~dp0..
python scripts\connector_registry_preflight_l666.py %*
