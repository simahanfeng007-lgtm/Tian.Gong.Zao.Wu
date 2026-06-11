@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0..\project"
set "STATE_DIR=%TEMP%\linyuanzhe_prompt_trace_%RANDOM%_%RANDOM%"
set "LINYUANZHE_STATE_DIR=%STATE_DIR%"
set "TIANGONG_STATE_DIR=%STATE_DIR%"
set "TIANGONG_SOUL_BASELINE_PATH=%STATE_DIR%\soul\soul_emotion_baseline.json"
set "TIANGONG_PROMPT_TRACE_FILE=%STATE_DIR%\prompt_trace\prompt_trace.jsonl"
set "TIANGONG_PROMPT_TUNER_FILE=%STATE_DIR%\prompt_trace\prompt_tuning_state.json"
set "PYTHONDONTWRITEBYTECODE=1"
set PYTHONPATH=.
python -S -B run_prompt_trace_smoke_l67214.py
set "RC=%ERRORLEVEL%"
if exist "%STATE_DIR%" rmdir /s /q "%STATE_DIR%" >nul 2>nul
exit /b %RC%
