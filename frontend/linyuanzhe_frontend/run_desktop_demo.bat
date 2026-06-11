@echo off
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PROBE=%~dp0..\..\00_ASCII_START_HERE\python\PYTHON_PROBE_L67217.py"
if not exist "%PROBE%" (
  echo [Linyuanzhe] Python probe missing: %PROBE%
  pause
  exit /b 23
)
echo [Linyuanzhe] Deprecated mock desktop demo wrapper...
call :find_python_tk
if errorlevel 1 (
  pause
  exit /b 1
)
"%PYTHON_EXE%" -S -B run_desktop_demo.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo [Linyuanzhe] Deprecated wrapper returned non-zero. Use START_FROM_ANYWHERE_AUTO or 01_启动入口.
  pause
)
exit /b %RC%

:find_python_tk
set "PYTHON_EXE="
call :try_python "py -3.12" "--require-tk"
if defined PYTHON_EXE exit /b 0
call :try_python "py -3.11" "--require-tk"
if defined PYTHON_EXE exit /b 0
call :try_python "py -3.10" "--require-tk"
if defined PYTHON_EXE exit /b 0
call :try_python "py -3" "--require-tk"
if defined PYTHON_EXE exit /b 0
call :try_python "python" "--require-tk"
if defined PYTHON_EXE exit /b 0
echo [Linyuanzhe] Python 3 + tkinter not found. Install Python 3.10-3.14 with Tcl/Tk enabled.
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
