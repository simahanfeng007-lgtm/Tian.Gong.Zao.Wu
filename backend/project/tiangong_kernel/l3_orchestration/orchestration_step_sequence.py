"""L3 第二阶段 Step 序列与 Step 转移建议对象。

本模块只描述步骤顺序、候选转移、准备度事实和续接建议引用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind
from .orchestration_progress import StepProgressSnapshot


class StepTransitionKind(str, Enum):
    """Step 转移类别。"""

    UNKNOWN = "unknown"
    CONTINUE_CURRENT = "continue_current"
    ADVANCE_NEXT = "advance_next"
    WAIT_MISSING_STATE = "wait_missing_state"
    PAUSE = "pause"
    BLOCK_FOR_REVIEW = "block_for_review"
    RESUME = "resume"
    CANCEL = "cancel"
    RECOVER = "recover"


@dataclass(frozen=True, slots=True)
class StepSequence:
    """Step 序列事实。"""

    sequence_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    completed_step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    active_step_ref: TypedRef | None = None
    next_step_ref: TypedRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    sequence_notes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.completed_step_refs) > len(self.step_refs):
            raise ValueError("StepSequence.completed_step_refs cannot exceed step_refs")
        if self.active_step_ref is not None and self.step_refs and self.active_step_ref not in self.step_refs:
            raise ValueError("StepSequence.active_step_ref must be included in step_refs")
        if self.next_step_ref is not None and self.step_refs and self.next_step_ref not in self.step_refs:
            raise ValueError("StepSequence.next_step_ref must be included in step_refs")
        if any(len(item) > 256 for item in self.sequence_notes):
            raise ValueError("StepSequence.sequence_notes entries must be short")
        if not self.schema_version:
            raise ValueError("StepSequence.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepTransitionCandidate:
    """Step 转移候选事实。"""

    candidate_ref: TypedRef | None = None
    sequence_ref: TypedRef | None = None
    source_step_ref: TypedRef | None = None
    target_step_ref: TypedRef | None = None
    transition_kind: StepTransitionKind = StepTransitionKind.UNKNOWN
    intent: LifecycleTransitionIntent = LifecycleTransitionIntent.UNKNOWN
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    candidate_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    required_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    score_hint: float = 0.0
    advisory_only: bool = True
    reason_items: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.score_hint <= 1.0:
            raise ValueError("StepTransitionCandidate.score_hint must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("StepTransitionCandidate.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("StepTransitionCandidate.missing_state_fields entries must be short")
        if any(len(item) > 256 for item in self.reason_items):
            raise ValueError("StepTransitionCandidate.reason_items entries must be short")
        if not self.schema_version:
            raise ValueError("StepTransitionCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepTransitionAdvice:
    """Step 转移建议。

    作用：表达从当前 step 到候选 step 的建议、阻断项和需要补充的状态字段。
    边界：不推进 step，不调用工具，不生成执行请求。
    """

    advice_ref: TypedRef | None = None
    candidate: StepTransitionCandidate | None = None
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    l2_state_update_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l5_boundary_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l6_service_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.transition_score <= 1.0:
            raise ValueError("StepTransitionAdvice.transition_score must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("StepTransitionAdvice.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("StepTransitionAdvice.missing_state_fields entries must be short")
        if len(self.reason_summary) > 512:
            raise ValueError("StepTransitionAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StepTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepReadinessEvaluation:
    """Step 准备度评估事实。"""

    evaluation_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    progress_snapshot: StepProgressSnapshot | None = None
    readiness_score_ref: TypedRef | None = None
    readiness_score_value: float = 0.0
    required_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.readiness_score_value <= 1.0:
            raise ValueError("StepReadinessEvaluation.readiness_score_value must be between 0.0 and 1.0")
        if self.advisory_only is not True:
            raise ValueError("StepReadinessEvaluation.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("StepReadinessEvaluation.missing_state_fields entries must be short")
        if len(self.reason_summary) > 512:
            raise ValueError("StepReadinessEvaluation.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StepReadinessEvaluation.schema_version cannot be empty")
