@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动临渊者桌面端：前端 + 本地桥接后端 + 当前进程内存中的真实模型配置
echo 注意：密钥只保存在本次窗口进程内存，不写入包体、报告或日志。
set /p LINYUANZHE_PROVIDER_BASE=请输入 OpenAI-compatible Base URL: 
set /p LINYUANZHE_PROVIDER_KEY=请输入 Provider Key: 
set /p LINYUANZHE_MODEL=请输入模型名，默认 deepseek-reasoner: 
if "%LINYUANZHE_MODEL%"=="" set LINYUANZHE_MODEL=deepseek-reasoner
set LINYUANZHE_PROVIDER=deepseek
python desktop\start_linyuanzhe_desktop_l671.py --backend-mode provider
if errorlevel 1 (
  echo.
  echo 启动失败。请运行 一键自检_L6701.bat 查看原因。
  pause
)
