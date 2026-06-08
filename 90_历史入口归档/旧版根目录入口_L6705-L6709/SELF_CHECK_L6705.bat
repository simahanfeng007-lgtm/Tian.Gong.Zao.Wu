@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
echo 临渊者桌面端前后端一体化包自检 L6.70.6
call :find_python
if not defined LZ_PY goto no_python
echo 使用 Python：%LZ_PY%
%LZ_PY% scripts\desktop_bundle_preflight_l671.py
set EXITCODE=%ERRORLEVEL%
echo.
echo 自检退出码：%EXITCODE%
echo 报告路径：reports\desktop_bundle_preflight_l671.json
pause
exit /b %EXITCODE%

:find_python
for %%C in ("py -3.12" "py -3.11" "py -3.10" "python" "python3") do call :try_python %%~C
exit /b

:try_python
if defined LZ_PY exit /b
set "CAND=%*"
%CAND% -c "import sys; sys.exit(2) if sys.version_info < (3,10) else None; import tkinter as tk; r=tk.Tk(); r.withdraw(); r.destroy()" >nul 2>nul
if not errorlevel 1 set "LZ_PY=%CAND%"
exit /b

:no_python
echo 未找到可用的 Python 3.10+ Tcl/Tk 桌面环境。
echo 建议安装官方 Python 3.12/3.11，并在安装器中勾选 Tcl/Tk and IDLE。
echo 当前机器如果只有 Python315 且报 Can't find a usable tk.tcl，说明该解释器不能启动 Tk 桌面端。
pause
exit /b 12
