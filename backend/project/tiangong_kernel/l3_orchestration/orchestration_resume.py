"""L3 第二阶段续接、恢复、中断建议对象。

这些对象只给出 Run / Task / Step 的续接建议，不执行恢复，不取消流程，不触发下游层。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_continuity import RecoveryPriorityScore, ResumabilityIndex, StepReadinessScore
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class ResumeAdviceKind(str, Enum):
    """续接建议类别。"""

    UNKNOWN = "unknown"
    RESUME_CURRENT = "resume_current"
    RESUME_NEXT_STEP = "resume_next_step"
    WAIT_MISSING_STATE = "wait_missing_state"
    RECOVER_FROM_FAILURE = "recover_from_failure"
    CANCEL_OR_ABANDON = "cancel_or_abandon"


@dataclass(frozen=True, slots=True)
class StepResumeAdvice:
    """Step 续接建议。"""

    advice_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    next_step_ref: TypedRef | None = None
    advice_kind: ResumeAdviceKind = ResumeAdviceKind.UNKNOWN
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    intent: LifecycleTransitionIntent = LifecycleTransitionIntent.UNKNOWN
    readiness_score: StepReadinessScore | None = None
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("StepResumeAdvice.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("StepResumeAdvice.missing_state_fields entries must be short")
        if len(self.reason_summary) > 512:
            raise ValueError("StepResumeAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StepResumeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskResumeAdvice:
    """Task 续接建议。"""

    advice_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    active_step_ref: TypedRef | None = None
    advice_kind: ResumeAdviceKind = ResumeAdviceKind.UNKNOWN
    resumability_index: ResumabilityIndex | None = None
    step_resume_advices: tuple[StepResumeAdvice, ...] = field(default_factory=tuple)
    recovery_priority: RecoveryPriorityScore | None = None
    future_l5_boundary_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("TaskResumeAdvice.advisory_only must remain true in L3 phase 2")
        if len(self.reason_summary) > 512:
            raise ValueError("TaskResumeAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TaskResumeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskInterruptionAdvice:
    """Task 中断处理建议。"""

    advice_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    interruption_reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    suggested_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.UNKNOWN
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("TaskInterruptionAdvice.advisory_only must remain true in L3 phase 2")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("TaskInterruptionAdvice.missing_state_fields entries must be short")
        if len(self.reason_summary) > 512:
            raise ValueError("TaskInterruptionAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TaskInterruptionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunResumeAdvice:
    """Run 续接建议。"""

    advice_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    active_task_ref: TypedRef | None = None
    advice_kind: ResumeAdviceKind = ResumeAdviceKind.UNKNOWN
    resumability_index: ResumabilityIndex | None = None
    task_resume_advices: tuple[TaskResumeAdvice, ...] = field(default_factory=tuple)
    recovery_priority: RecoveryPriorityScore | None = None
    future_l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l5_boundary_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l6_service_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("RunResumeAdvice.advisory_only must remain true in L3 phase 2")
        if len(self.reason_summary) > 512:
            raise ValueError("RunResumeAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RunResumeAdvice.schema_version cannot be empty")
