@echo off
setlocal
cd /d "%~dp0"
if "%LINYUANZHE_RUNTIME_URL%"=="" set LINYUANZHE_RUNTIME_URL=http://127.0.0.1:8787
echo [临渊者] 启动 FE.01 STEP13 Runtime SSE 接线模式：%LINYUANZHE_RUNTIME_URL%
py -3 run_runtime_sse_demo.py
if errorlevel 1 (
  echo [临渊者] py -3 不可用，尝试 python...
  python run_runtime_sse_demo.py
)
if errorlevel 1 (
  echo [临渊者] 启动失败。请确认 Runtime 网关地址正确，且当前环境支持 tkinter 桌面窗口。
  pause
  exit /b 1
)
endlocal
