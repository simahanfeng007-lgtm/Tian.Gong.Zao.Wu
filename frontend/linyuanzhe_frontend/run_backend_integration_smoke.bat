@echo off
cd /d %~dp0\..
python -m linyuanzhe_frontend.run_backend_integration_smoke %*
