from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_action_grounding import SkillToolReleaseSessionContext


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l4_skill_tool_release_session_context_links_required_refs():
    context = SkillToolReleaseSessionContext(
        skill_ref=typed(10, "skill"),
        tool_group_ref=typed(11, "tool_group"),
        release_ref=typed(12, "release"),
        permit_ref=typed(13, "permit"),
        l5_review_hint_ref=typed(14, "l5_review_hint"),
    )
    assert context.skill_ref is not None
    assert context.tool_group_ref is not None
    assert context.release_ref is not None
    assert context.permit_ref is not None
    assert context.l5_review_hint_ref is not None
    assert context.context_only is True
    assert context.reference_only is True
    assert context.no_real_tool_handle is True
    assert context.calls_model_or_tool is False
