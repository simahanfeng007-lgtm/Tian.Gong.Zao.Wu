import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_tool_shell_file_network_call_scan():
    bad = scan_l6_phase5_text('test:l6_phase5_bad_tool', 'subprocess and Path.write_text and socket.')
    assert bad.passed is False
    assert bad.p0_count >= 1
