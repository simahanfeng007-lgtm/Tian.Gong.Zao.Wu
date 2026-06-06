import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *


def test_forbidden_scan_blocks_model_http_tool_state():
    clean = scan_l6_phase4_text("l6:clean", "projection review candidate only")
    assert clean.passed is True
    dirty_text = "\n".join(["import openai", "requests.get(\'x\')", "base_url=\'x\'", "api_key=\'x\'", "subprocess", "write_fact", "save_memory", "dispatch_tool"])
    dirty = scan_l6_phase4_text("l6:dirty", dirty_text)
    assert dirty.passed is False
    assert dirty.p0_count >= 7
