@echo off
cd /d %~dp0..
python scripts\verify_l666_release.py %*
