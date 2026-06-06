from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_action_grounding import ToolResultReturnContext


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l4_tool_result_return_context_links_model_and_l3_continuation_refs():
    context = ToolResultReturnContext(
        tool_call_ref=typed(20, "tool_call"),
        tool_action_result_ref=typed(21, "tool_action_result"),
        tool_result_envelope_ref=typed(22, "tool_result_envelope"),
        model_continuation_ref=typed(23, "model_continuation"),
        l3_replan_suggestion_ref=typed(24, "l3_replan_suggestion"),
        l2_state_update_suggestion_ref=typed(25, "l2_state_update_suggestion"),
    )
    assert context.tool_call_ref is not None
    assert context.tool_action_result_ref is not None
    assert context.model_continuation_ref is not None
    assert context.l3_replan_suggestion_ref is not None
    assert context.context_only is True
    assert context.reference_only is True
    assert context.calls_model_or_tool is False
    assert context.writes_l2_state is False
