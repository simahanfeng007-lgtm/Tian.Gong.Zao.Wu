@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
echo [Tiangong v2.0] DataUp safe update
call :find_python
if errorlevel 1 (
  pause
  exit /b 1
)
"%PYTHON_EXE%" "%ROOT%\00_ASCII_START_HERE\python\START_DESKTOP_L6710.py" --dataup %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo [Tiangong] DataUp failed with exit code %RC%.
  pause
  exit /b %RC%
)
echo [Tiangong] DataUp completed.
exit /b 0

:find_python
set "PYTHON_EXE="
for %%V in (3.12 3.11 3.10 3.9 3) do (
  py -%%V --version >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=py -%%V"
    exit /b 0
  )
)
python --version >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_EXE=python"
  exit /b 0
)
echo [Tiangong] Python 3 not found. Install Python 3.10-3.12.
exit /b 1
