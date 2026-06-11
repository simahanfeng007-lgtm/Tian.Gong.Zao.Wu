@echo off
rem GENERATED_BY={{GENERATOR_ID}}
rem ENTRY_KIND={{ENTRY_KIND}}
rem TEMPLATE={{TEMPLATE_NAME}}
rem Q20_FIX=windows_double_click_safe_launcher
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
set "SCRIPT_VERSION={{VERSION}}"
set "SCRIPT_DIR=%~dp0"
set "START_DIR=%CD%"
set "TITLE={{TITLE}}"
set "SAFE_LAUNCHER="
title %TITLE%

call :find_safe_launcher
if not defined SAFE_LAUNCHER (
  echo [Linyuanzhe] Windows safe launcher missing.
  echo [Linyuanzhe] Fully extract the ZIP first. Keep 00_ASCII_START_HERE, desktop, frontend and backend together.
  echo [Linyuanzhe] Then run this BAT from inside the extracted folder.
  pause
  exit /b 20
)

set "PY_CMD="
call :try_python "py -3.14"
call :try_python "py -3.13"
call :try_python "py -3.12"
call :try_python "py -3.11"
call :try_python "py -3.10"
call :try_python "py -3"
call :try_python "python"

if not defined PY_CMD (
  echo [Linyuanzhe] Python 3.10-3.14 not found.
  echo [Linyuanzhe] Install Python from python.org, then enable Add python.exe to PATH and Tcl/Tk.
  pause
  exit /b 1
)

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONNOUSERSITE=1"

echo [Linyuanzhe] %TITLE%
echo [Linyuanzhe] Using Windows safe launcher.
%PY_CMD% -S -B -u "%SAFE_LAUNCHER%" --entry-kind "{{ENTRY_KIND}}" --python-entry "{{PY_ENTRY_WIN}}" --title "{{TITLE}}" --python-mode "{{PYTHON_MODE}}" --launcher-dir "%SCRIPT_DIR%" --start-dir "%START_DIR%" {{EXTRA_ARGS}}
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo [Linyuanzhe] Launch failed. Exit code %RC%.
  echo [Linyuanzhe] See the log path printed above. The window will stay open.
  pause
)
if /I "%LINYUANZHE_ALWAYS_PAUSE%"=="1" pause
exit /b %RC%

:try_python
if defined PY_CMD exit /b 0
%~1 -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,14) else 1)" >nul 2>nul
if not errorlevel 1 set "PY_CMD=%~1"
exit /b 0

:find_safe_launcher
call :try_safe "%SCRIPT_DIR%WIN_SAFE_LAUNCHER_L6738.py"
call :try_safe "%SCRIPT_DIR%..\python\WIN_SAFE_LAUNCHER_L6738.py"
call :try_safe "%SCRIPT_DIR%..\..\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
call :try_safe "%SCRIPT_DIR%00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
call :try_safe "%START_DIR%\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
if defined USERPROFILE (
  call :try_safe "%USERPROFILE%\Desktop\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
  call :try_safe "%USERPROFILE%\Downloads\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
  call :try_safe "%USERPROFILE%\Documents\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
  for /D %%D in ("%USERPROFILE%\Desktop\tiangong_v2_linyuanzhe*") do call :try_safe "%%~fD\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
  for /D %%D in ("%USERPROFILE%\Downloads\tiangong_v2_linyuanzhe*") do call :try_safe "%%~fD\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
  for /D %%D in ("%USERPROFILE%\Documents\tiangong_v2_linyuanzhe*") do call :try_safe "%%~fD\00_ASCII_START_HERE\python\WIN_SAFE_LAUNCHER_L6738.py"
)
exit /b 0

:try_safe
if defined SAFE_LAUNCHER exit /b 0
if exist "%~f1" set "SAFE_LAUNCHER=%~f1"
exit /b 0
