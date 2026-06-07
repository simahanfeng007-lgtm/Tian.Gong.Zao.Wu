@echo off
setlocal
cd /d "%~dp0"
echo [临渊者] 启动 FE.01 桌面演示包...
py -3 run_desktop_demo.py
if errorlevel 1 (
  echo [临渊者] py -3 不可用，尝试 python...
  python run_desktop_demo.py
)
if errorlevel 1 (
  echo [临渊者] 启动失败。请确认已安装 Python 3，且当前环境支持 tkinter 桌面窗口。
  pause
  exit /b 1
)
endlocal
