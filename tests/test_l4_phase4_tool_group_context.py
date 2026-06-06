from l4_phase4_builders import tool_group_context
from tiangong_kernel.l4_action_grounding import ToolGroupActionContext, action_grounding_stable_hash


def test_l4_phase4_tool_group_context_only_carries_refs():
    context = tool_group_context()
    assert isinstance(context, ToolGroupActionContext)
    assert context.context_only is True
    assert context.resolves_skill is False
    assert context.registers_tool is False
    assert context.grants_tool_permission is False
    assert len(context.available_tool_refs) == 1
    assert action_grounding_stable_hash(context)
