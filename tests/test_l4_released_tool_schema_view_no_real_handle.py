from pathlib import Path

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_action_grounding import ModelVisibleReleasedToolView, ReleasedToolSchemaView


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l4_released_tool_schema_views_are_ref_only_without_real_handles():
    view = ReleasedToolSchemaView(
        skill_ref=typed(1, "skill"),
        tool_group_ref=typed(2, "tool_group"),
        release_ref=typed(3, "tool_group_release"),
        tool_schema_refs=(typed(4, "tool_schema"),),
        permit_refs=(typed(5, "permit"),),
    )
    visible = ModelVisibleReleasedToolView(
        released_schema_view_ref=view.schema_view_ref,
        visible_tool_schema_refs=view.tool_schema_refs,
    )
    assert view.contains_real_tool_handle is False
    assert view.registers_tool is False
    assert view.calls_model_or_tool is False
    assert view.signs_permit is False
    assert visible.contains_real_tool_handle is False
    assert visible.calls_model_or_tool is False


def test_l4_released_tool_schema_source_has_no_real_execution_entrypoints():
    source = Path("tiangong_kernel/l4_action_grounding/released_tool_schema_view.py").read_text(encoding="utf-8")
    forbidden = ("callable", "handler", "client", "executor", "registry", "open(", "subprocess", "requests")
    for token in forbidden:
        assert token not in source
