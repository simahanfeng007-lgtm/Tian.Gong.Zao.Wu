@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
set "ENTRY=%ROOT%\00_ASCII_START_HERE\python\SELF_CHECK_L6710.py"
cd /d "%ROOT%"
echo [天工造物 v2.0] self check
call :find_python_tk
if errorlevel 1 (
  pause
  exit /b 1
)
"%PYTHON_EXE%" "%ENTRY%" %*
set "RC=%ERRORLEVEL%"
pause
exit /b %RC%

:find_python_tk
set "PYTHON_EXE="
call :try_python_tk py -3.12
if defined PYTHON_EXE exit /b 0
call :try_python_tk py -3.11
if defined PYTHON_EXE exit /b 0
call :try_python_tk py -3.10
if defined PYTHON_EXE exit /b 0
call :try_python_tk py -3.9
if defined PYTHON_EXE exit /b 0
call :try_python_tk py -3
if defined PYTHON_EXE exit /b 0
call :try_python_tk python
if defined PYTHON_EXE exit /b 0
echo [临渊者] 未找到可用的 Python 3 + tkinter。请安装 Python 3.10-3.12 并勾选 Tcl/Tk。
exit /b 1

:try_python_tk
for /f "usebackq delims=" %%E in (`%* -c "import sys, tkinter; print(sys.executable)" 2^>nul`) do (
  set "PYTHON_EXE=%%E"
  exit /b 0
)
exit /b 1
