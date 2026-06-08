@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python scripts\real_runtime_endpoint_smoke_l670.py --require-real
