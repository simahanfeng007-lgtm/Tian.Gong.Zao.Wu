@echo off
chcp 65001 >nul
cd /d %~dp0..
python launchers\start_linyuanzhe_rc.py %*
