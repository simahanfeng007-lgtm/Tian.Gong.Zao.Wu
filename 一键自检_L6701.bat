@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 临渊者桌面端前后端一体化包自检 L6.70.1
python scripts\desktop_bundle_preflight_l671.py
set EXITCODE=%ERRORLEVEL%
echo.
echo 自检退出码：%EXITCODE%
echo 报告路径：reports\desktop_bundle_preflight_l671.json
pause
exit /b %EXITCODE%
