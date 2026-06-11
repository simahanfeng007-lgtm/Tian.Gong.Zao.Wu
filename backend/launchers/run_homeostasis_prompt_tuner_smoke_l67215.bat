@echo off
set "PYTHONDONTWRITEBYTECODE=1"
setlocal
cd /d "%~dp0..\project"
python -S -B run_homeostasis_prompt_tuner_smoke_l67215.py
endlocal
