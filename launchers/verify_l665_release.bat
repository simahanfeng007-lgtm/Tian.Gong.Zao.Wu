@echo off
chcp 65001 >nul
cd /d %~dp0..
python scripts\verify_l665_release.py %*
