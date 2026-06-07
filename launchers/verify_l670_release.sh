#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 scripts/verify_l670_release.py
