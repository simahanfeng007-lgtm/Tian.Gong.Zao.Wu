import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_forbidden_scan_blocks_sdk_http_secret_write():
    report = scan_l6_phase5_text('test:l6_phase5_forbidden_combo', 'import deepseek\nhttpx.\nsave_secret\nwrite_audit\ncharge_budget')
    assert report.passed is False
    assert report.p0_count >= 5
