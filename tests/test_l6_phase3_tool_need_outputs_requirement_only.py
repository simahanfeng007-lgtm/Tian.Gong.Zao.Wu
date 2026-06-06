import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_tool_need_outputs_requirement_only():
    need = MindToolNeed(source_plugin_ref="mind:attention_mind")
    assert need.requirement_only is True
    assert need.invokes_tool is False
    assert need.requirement.requirement_only is True
    with pytest.raises(ValueError):
        MindToolNeed(invokes_tool=True)
