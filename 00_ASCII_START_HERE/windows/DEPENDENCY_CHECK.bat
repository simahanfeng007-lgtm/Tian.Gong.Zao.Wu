@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
set "CHECKER=%ROOT%\00_ASCII_START_HERE\python\DEPENDENCY_CHECK.py"

echo [Tiangong v2.0] Dependency check
call :find_python
if errorlevel 1 (
  pause
  exit /b 1
)

"%PYTHON_EXE%" "%CHECKER%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%

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
echo [Tiangong] Python not found. Install Python 3.10-3.12.
echo Download: https://www.python.org/downloads/
exit /b 1
