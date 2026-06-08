@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
echo [临渊者] DataUp 一键安全更新 - L6.71.9 修复版
call :find_python
if errorlevel 1 (
  pause
  exit /b 1
)
"%PYTHON_EXE%" "desktop\dataup_update_helper_l6717.py" --source auto --apply --yes
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [临渊者] DataUp 更新失败，退出码 %RC%。未确认成功前不要覆盖旧版本。
  pause
  exit /b %RC%
)
echo [临渊者] DataUp 更新完成。
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
