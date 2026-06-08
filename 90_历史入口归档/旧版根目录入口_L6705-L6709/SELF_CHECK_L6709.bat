@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo [临渊者] SELF_CHECK_L6709.bat L6709 历史入口自检
call :find_python_tk
if errorlevel 1 (
  pause
  exit /b 1
)
"%PYTHON_EXE%" SELF_CHECK_L6709.py %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo [临渊者] 自检失败，退出码 %RC%。
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
echo [临渊者] 未找到可用的 Python 3 + tkinter。
exit /b 1

:try_python_tk
for /f "usebackq delims=" %%E in (`%* -c "import sys, tkinter; print(sys.executable)" 2^>nul`) do (
  set "PYTHON_EXE=%%E"
  exit /b 0
)
exit /b 1
