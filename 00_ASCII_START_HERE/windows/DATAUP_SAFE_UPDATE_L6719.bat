@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
echo [天工造物 v2.0] DataUp safe update
call :find_python
if errorlevel 1 (
  pause
  exit /b 1
)
"%PYTHON_EXE%" "desktop\dataup_update_helper_l6717.py" --source auto --apply --yes
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo [天工造物 v2.0] DataUp failed with exit code %RC%.
  pause
  exit /b %RC%
)
echo [天工造物 v2.0] DataUp completed.
pause
exit /b 0

:find_python
set "PYTHON_EXE="
call :try_python py -3.12
if defined PYTHON_EXE exit /b 0
call :try_python py -3.11
if defined PYTHON_EXE exit /b 0
call :try_python py -3.10
if defined PYTHON_EXE exit /b 0
call :try_python py -3.9
if defined PYTHON_EXE exit /b 0
call :try_python py -3
if defined PYTHON_EXE exit /b 0
call :try_python python
if defined PYTHON_EXE exit /b 0
echo [临渊者] 未找到可用的 Python 3。请安装 Python 3.10-3.12。
exit /b 1

:try_python
for /f "usebackq delims=" %%E in (`%* -c "import sys; print(sys.executable)" 2^>nul`) do (
  set "PYTHON_EXE=%%E"
  exit /b 0
)
exit /b 1
