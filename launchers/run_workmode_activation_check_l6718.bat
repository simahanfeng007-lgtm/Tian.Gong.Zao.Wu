@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\..\backend\project"
call :find_python
if errorlevel 1 exit /b 1
"%PYTHON_EXE%" run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate status"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "asset-activate smoke 工作模式确认"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" run_agent.py --mock --tool-mode runtime_governed --workspace . --max-steps 8 --once "runtime-tools align"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" -m compileall -q tiangong_agent_runtime tiangong_agent_shell .linyuanzhe\active_assets tests
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" -m pytest -q
exit /b %errorlevel%

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
