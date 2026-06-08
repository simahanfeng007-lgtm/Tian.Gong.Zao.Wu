@echo off
chcp 65001 >nul
cd /d %~dp0..
python scripts\real_runtime_gate_l660.py --require-real %*
