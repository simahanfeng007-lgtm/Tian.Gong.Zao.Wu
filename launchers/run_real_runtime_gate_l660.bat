@echo off
cd /d %~dp0..
python scripts\real_runtime_gate_l660.py --require-real %*
