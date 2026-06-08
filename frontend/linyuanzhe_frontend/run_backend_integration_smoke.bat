@echo off
chcp 65001 >nul
cd /d %~dp0\..
python -m linyuanzhe_frontend.run_backend_integration_smoke %*
