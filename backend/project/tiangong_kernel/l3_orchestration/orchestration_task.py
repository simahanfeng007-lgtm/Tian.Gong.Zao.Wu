"""L3 第二阶段 Task 编排对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionCandidate, OrchestrationLifecycleKind
from .orchestration_progress import TaskProgressSnapshot
from .orchestration_resume import TaskInterruptionAdvice, TaskResumeAdvice
from .orchestration_step_sequence import StepSequence
from .orchestration_transition_advice import ProcessStateTransitionAdvice


@dataclass(frozen=True, slots=True)
class TaskOrchestrationRef:
    """Task 编排引用。"""

    task_ref: TypedRef
    run_ref: TypedRef | None = None
    task_index: int = 0
    source_goal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.task_index < 0:
            raise ValueError("TaskOrchestrationRef.task_index cannot be negative")
        if not self.schema_version:
            raise ValueError("TaskOrchestrationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskContinuityEvaluation:
    """Task 连续性评估事实。"""

    evaluation_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    progress_snapshot: TaskProgressSnapshot | None = None
    step_sequence: StepSequence | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    transition_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("TaskContinuityEvaluation.advisory_only must remain true in L3 phase 2")
        if len(self.reason_summary) > 512:
            raise ValueError("TaskContinuityEvaluation.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TaskContinuityEvaluation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskOrchestrationPlan:
    """Task 编排计划事实。"""

    plan_ref: TypedRef | None = None
    task_ref: TaskOrchestrationRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    progress_snapshot: TaskProgressSnapshot | None = None
    step_sequence: StepSequence | None = None
    transition_candidates: tuple[LifecycleTransitionCandidate, ...] = field(default_factory=tuple)
    transition_advices: tuple[ProcessStateTransitionAdvice, ...] = field(default_factory=tuple)
    resume_advice: TaskResumeAdvice | None = None
    interruption_advice: TaskInterruptionAdvice | None = None
    continuity_evaluation_ref: TypedRef | None = None
    future_l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l5_boundary_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l6_service_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("TaskOrchestrationPlan.advisory_only must remain true in L3 phase 2")
        if len(self.summary) > 512:
            raise ValueError("TaskOrchestrationPlan.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TaskOrchestrationPlan.schema_version cannot be empty")
