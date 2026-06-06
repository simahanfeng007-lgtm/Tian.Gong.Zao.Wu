import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_declarations_inert():
    declarations = default_cognitive_continuity_plugin_declarations()
    assert len(declarations) >= 8
    assert all(item.is_runtime is False for item in declarations)
    assert all(item.dispatches_model is False for item in declarations)
    assert all(item.dispatches_tool is False for item in declarations)
    assert all(item.writes_l2_fact is False for item in declarations)
