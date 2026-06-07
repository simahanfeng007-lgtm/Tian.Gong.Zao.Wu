"""L3 第三阶段 Skill / ToolGroup 状态转移建议对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind
from .orchestration_transition_advice import L2StateUpdateSuggestion


class SkillToolTransitionKind(str, Enum):
    """Skill / ToolGroup 编排状态转移种类。"""

    UNKNOWN = "unknown"
    DISPLAY_TO_SELECTION = "display_to_selection"
    SELECTION_TO_ACTIVATION = "selection_to_activation"
    ACTIVATION_TO_TOOL_GROUP_RESOLVE = "activation_to_tool_group_resolve"
    TOOL_GROUP_RESOLVE_TO_RELEASE_ADVICE = "tool_group_resolve_to_release_advice"
    RELEASE_ADVICE_TO_REVIEW_WAIT = "release_advice_to_review_wait"
    PAUSE_FOR_CLARIFICATION = "pause_for_clarification"


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


@dataclass(frozen=True, slots=True)
class SkillToolStateTransitionSuggestion:
    """Skill / ToolGroup 编排状态转移建议；不修改 L2 或真实系统。"""

    suggestion_ref: TypedRef
    subject_ref: TypedRef
    transition_kind: SkillToolTransitionKind = SkillToolTransitionKind.UNKNOWN
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    l2_update_suggestions: tuple[L2StateUpdateSuggestion, ...] = field(default_factory=tuple)
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.transition_kind, SkillToolTransitionKind):
            raise ValueError("SkillToolStateTransitionSuggestion.transition_kind must use SkillToolTransitionKind")
        if not isinstance(self.current_lifecycle, OrchestrationLifecycleKind):
            raise ValueError("SkillToolStateTransitionSuggestion.current_lifecycle must use OrchestrationLifecycleKind")
        if not isinstance(self.suggested_lifecycle, OrchestrationLifecycleKind):
            raise ValueError("SkillToolStateTransitionSuggestion.suggested_lifecycle must use OrchestrationLifecycleKind")
        if not isinstance(self.transition_intent, LifecycleTransitionIntent):
            raise ValueError("SkillToolStateTransitionSuggestion.transition_intent must use LifecycleTransitionIntent")
        _ensure_unit_interval(self.transition_score, "SkillToolStateTransitionSuggestion.transition_score")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("SkillToolStateTransitionSuggestion.missing_state_fields entries must be short")
        _ensure_short_text(self.reason_summary, "SkillToolStateTransitionSuggestion.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolStateTransitionSuggestion.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolStateTransitionSuggestion.schema_version cannot be empty")
