@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
set "PROBE=%~dp0..\00_ASCII_START_HERE\python\PYTHON_PROBE_L67217.py"
if not exist "%PROBE%" (
  echo [Linyuanzhe] Python probe missing: %PROBE%
  exit /b 23
)
cd /d "%~dp0..\backend\project"
call :find_python
if errorlevel 1 exit /b 1
set "LINYUANZHE_STATE_DIR=%TEMP%\linyuanzhe_workmode_%RANDOM%_%RANDOM%"
set "TIANGONG_STATE_DIR=%LINYUANZHE_STATE_DIR%"
set "TIANGONG_SOUL_BASELINE_PATH=%LINYUANZHE_STATE_DIR%\soul\soul_emotion_baseline.json"
set "TIANGONG_PROMPT_TRACE_FILE=%LINYUANZHE_STATE_DIR%\prompt_trace\prompt_trace.jsonl"
set "TIANGONG_PROMPT_TUNER_FILE=%LINYUANZHE_STATE_DIR%\prompt_trace\prompt_tuning_state.json"
set "PYTHONDONTWRITEBYTECODE=1"
echo [Linyuanzhe] Python: %PYTHON_EXE%
"%PYTHON_EXE%" -S -B run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate status"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" -S -B run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate smoke workmode-confirm"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" -S -B run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "runtime-tools align"
if errorlevel 1 exit /b %errorlevel%
if exist .linyuanzhe\active_assets (
  "%PYTHON_EXE%" -S -B run_no_pyc_compile_check_l6738.py tiangong_agent_runtime tiangong_agent_shell .linyuanzhe\active_assets
) else (
  "%PYTHON_EXE%" -S -B run_no_pyc_compile_check_l6738.py tiangong_agent_runtime tiangong_agent_shell
)
if errorlevel 1 exit /b %errorlevel%
if exist tests (
  "%PYTHON_EXE%" -S -B -m pytest -q tests
  set "RC=%ERRORLEVEL%"
) else (
  echo SKIP: 净包不携带 pytest tests 目录；已完成 mock run_agent 与 no-pyc compile 验收。
  set "RC=0"
)
if exist "%LINYUANZHE_STATE_DIR%" rmdir /s /q "%LINYUANZHE_STATE_DIR%" >nul 2>nul
exit /b %RC%

:find_python
set "PYTHON_EXE="
call :try_python "py -3.12" ""
if defined PYTHON_EXE exit /b 0
call :try_python "py -3.11" ""
if defined PYTHON_EXE exit /b 0
call :try_python "py -3.10" ""
if defined PYTHON_EXE exit /b 0
call :try_python "py -3" ""
if defined PYTHON_EXE exit /b 0
call :try_python "python" ""
if defined PYTHON_EXE exit /b 0
echo [Linyuanzhe] Python 3 not found. Install Python 3.10-3.14.
exit /b 1

:try_python
set "PY_CMD=%~1"
set "PY_FLAG=%~2"
for /f "usebackq tokens=1,* delims==" %%A in (`%PY_CMD% -S -B "%PROBE%" %PY_FLAG% 2^>nul`) do (
  if /I "%%A"=="LINYUANZHE_PY_OK" if exist "%%B" (
    set "PYTHON_EXE=%%B"
    exit /b 0
  )
)
exit /b 1
