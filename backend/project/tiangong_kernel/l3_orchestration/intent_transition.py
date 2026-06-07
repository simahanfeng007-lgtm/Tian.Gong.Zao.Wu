"""L3 第四阶段意图状态转移投影对象。

本模块只把 ModelIntent / ToolIntent / ActionIntent 的转移建议归并为可审查投影。
它不写入状态，不发起边界审查，不发起执行准备请求。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import IntentKind
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class IntentTransitionKind(str, Enum):
    """意图状态转移类别。"""

    UNKNOWN = "unknown"
    MODEL_TO_TOOL_INTENT = "model_to_tool_intent"
    TOOL_TO_ACTION_INTENT = "tool_to_action_intent"
    INTENT_TO_CLARIFICATION = "intent_to_clarification"
    INTENT_TO_DOWNGRADE = "intent_to_downgrade"
    INTENT_TO_BOUNDARY_PREPARATION_HINT = "intent_to_boundary_preparation_hint"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class IntentTransitionProjection:
    """意图转移投影；只供后续阶段审查参考。"""

    projection_ref: TypedRef
    subject_intent_ref: TypedRef
    subject_intent_kind: IntentKind = IntentKind.UNKNOWN
    transition_kind: IntentTransitionKind = IntentTransitionKind.UNKNOWN
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    related_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "IntentTransitionProjection.transition_score")
        _ensure_short_text(self.reason_summary, "IntentTransitionProjection.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentTransitionProjection.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentTransitionProjection.schema_version cannot be empty")
