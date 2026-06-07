#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "临渊者桌面端前后端一体化包自检 L6.70.1"
python3 scripts/desktop_bundle_preflight_l671.py
