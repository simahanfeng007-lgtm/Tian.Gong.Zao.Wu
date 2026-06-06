import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_forbidden_scan_blocks_tool_file_shell_state_write_patterns():
    dirty = scan_l6_phase3_mind_text("mind:dirty2", "subprocess\nos.system\nPath.write_text\nwrite_l2_fact\nwrite_memory\nwrite_audit\ncharge_budget")
    assert dirty.passed is False
    assert dirty.p0_count >= 6
