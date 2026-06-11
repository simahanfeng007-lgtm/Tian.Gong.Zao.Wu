@echo off
set "PYTHONDONTWRITEBYTECODE=1"
setlocal
set ROOT_DIR=%~dp0..
cd /d "%ROOT_DIR%\backend\project"
if "%PYTHON_EXE%"=="" set PYTHON_EXE=python
"%PYTHON_EXE%" -S -B run_prompt_tuner_stability_guard_smoke_l67216.py
exit /b %ERRORLEVEL%
