"""L4 Skill direct display and ToolGroup release chain index."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class SkillToolReleaseChainIndex:
    """Skill 直显到工具结果返回链路索引，只列映射与顺序。"""

    chain_index_ref: TypedRef | None = None
    chain_steps: tuple[str, ...] = (
        "skill_projection_exposure",
        "skill_request_selection",
        "skill_authorization_l5_review_hint",
        "tool_group_release",
        "released_tool_schema_view",
        "tool_call_envelope",
        "tool_result_return",
        "model_continuation_l3_replan",
        "l2_state_update_suggestion",
    )
    l1_object_names: tuple[str, ...] = field(default_factory=tuple)
    l2_object_names: tuple[str, ...] = field(default_factory=tuple)
    l3_object_names: tuple[str, ...] = field(default_factory=tuple)
    l4_object_names: tuple[str, ...] = (
        "ReleasedToolSchemaView",
        "ModelVisibleReleasedToolView",
        "SkillToolReleaseSessionContext",
        "ToolResultReturnContext",
    )
    handoff_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    index_only: bool = True
    reference_only: bool = True
    no_action: bool = True
    no_permission_decision: bool = True
    no_real_tool_handle: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.chain_steps + self.l1_object_names + self.l2_object_names + self.l3_object_names + self.l4_object_names:
            ensure_short_text(item, "SkillToolReleaseChainIndex text", 128)
        ensure_true(self.index_only, "SkillToolReleaseChainIndex.index_only")
        ensure_true(self.reference_only, "SkillToolReleaseChainIndex.reference_only")
        ensure_true(self.no_action, "SkillToolReleaseChainIndex.no_action")
        ensure_true(self.no_permission_decision, "SkillToolReleaseChainIndex.no_permission_decision")
        ensure_true(self.no_real_tool_handle, "SkillToolReleaseChainIndex.no_real_tool_handle")
        ensure_false(False, "SkillToolReleaseChainIndex.reserved_false_guard")
        ensure_schema_version(self.schema_version, "SkillToolReleaseChainIndex.schema_version")
