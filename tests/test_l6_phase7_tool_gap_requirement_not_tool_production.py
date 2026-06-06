import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import ToolGapRequirement

def test_tool_gap_requirement_not_tool_production():
    req = ToolGapRequirement()
    assert req.produces_tool is False
    with pytest.raises(ValueError):
        ToolGapRequirement(produces_tool=True)
