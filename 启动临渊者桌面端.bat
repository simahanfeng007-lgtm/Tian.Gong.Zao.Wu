@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动临渊者桌面端：前端 + 本地桥接后端
python desktop\start_linyuanzhe_desktop_l671.py --backend-mode mock
if errorlevel 1 (
  echo.
  echo 启动失败。请先确认本机已安装 Python 3.10+，并运行 一键自检_L6701.bat 查看原因。
  pause
)
