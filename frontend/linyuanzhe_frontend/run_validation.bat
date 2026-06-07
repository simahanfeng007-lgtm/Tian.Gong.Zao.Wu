@echo off
setlocal
cd /d "%~dp0"
echo [临渊者] 验证 FE.01 STEP15 / L6.54 顺滑层包...
py -3 scripts\validate_demo_package.py
if errorlevel 1 (
  echo [临渊者] py -3 不可用或验证失败，尝试 python...
  python scripts\validate_demo_package.py
)
if errorlevel 1 (
  echo [临渊者] 验证失败。
  pause
  exit /b 1
)
echo [临渊者] 验证通过。
pause
endlocal
