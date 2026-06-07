@echo off
cd /d %~dp0..
python scripts\verify_l665_release.py %*
