"""L4 Skill and ToolGroup release read-only contexts."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class SkillToolReleaseSessionContext:
    """Skill 直显与 ToolGroup 释放会话上下文，只保存链路引用。"""

    session_context_ref: TypedRef | None = None
    skill_projection_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    skill_request_ref: TypedRef | None = None
    skill_selection_ref: TypedRef | None = None
    skill_authorization_ref: TypedRef | None = None
    l5_review_hint_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    release_ref: TypedRef | None = None
    permit_ref: TypedRef | None = None
    released_tool_schema_view_ref: TypedRef | None = None
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    context_only: bool = True
    reference_only: bool = True
    no_real_tool_handle: bool = True
    calls_model_or_tool: bool = False
    signs_permit: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            ensure_short_text(item, "SkillToolReleaseSessionContext.reason_codes", 128)
        ensure_true(self.context_only, "SkillToolReleaseSessionContext.context_only")
        ensure_true(self.reference_only, "SkillToolReleaseSessionContext.reference_only")
        ensure_true(self.no_real_tool_handle, "SkillToolReleaseSessionContext.no_real_tool_handle")
        ensure_false(self.calls_model_or_tool, "SkillToolReleaseSessionContext.calls_model_or_tool")
        ensure_false(self.signs_permit, "SkillToolReleaseSessionContext.signs_permit")
        ensure_schema_version(self.schema_version, "SkillToolReleaseSessionContext.schema_version")


@dataclass(frozen=True, slots=True)
class ToolResultReturnContext:
    """工具结果返回上下文，只链接工具调用、结果与续接引用。"""

    return_context_ref: TypedRef | None = None
    tool_call_ref: TypedRef | None = None
    tool_action_result_ref: TypedRef | None = None
    tool_result_envelope_ref: TypedRef | None = None
    model_continuation_ref: TypedRef | None = None
    l3_replan_suggestion_ref: TypedRef | None = None
    l2_state_update_suggestion_ref: TypedRef | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    context_only: bool = True
    reference_only: bool = True
    result_wrapper_only: bool = True
    calls_model_or_tool: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.context_only, "ToolResultReturnContext.context_only")
        ensure_true(self.reference_only, "ToolResultReturnContext.reference_only")
        ensure_true(self.result_wrapper_only, "ToolResultReturnContext.result_wrapper_only")
        ensure_false(self.calls_model_or_tool, "ToolResultReturnContext.calls_model_or_tool")
        ensure_false(self.writes_l2_state, "ToolResultReturnContext.writes_l2_state")
        ensure_schema_version(self.schema_version, "ToolResultReturnContext.schema_version")
