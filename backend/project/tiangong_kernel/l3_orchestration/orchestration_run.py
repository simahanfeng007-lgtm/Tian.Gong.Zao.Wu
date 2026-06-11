"""L3 第二阶段 Run 编排对象。

Run 对象只表达流程视图、计划和连续性评估引用，不实现真实运行循环。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state.projection_state import RuntimeSliceProjectionState

from .orchestration_context import OrchestrationContext
from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionCandidate, OrchestrationLifecycleKind
from .orchestration_progress import RunProgressSnapshot
from .orchestration_resume import RunResumeAdvice
from .orchestration_transition_advice import ProcessStateTransitionAdvice


@dataclass(frozen=True, slots=True)
class RunOrchestrationRef:
    """Run 编排引用。"""

    run_ref: TypedRef
    source_request_ref: TypedRef | None = None
    source_context_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RunOrchestrationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunOrchestrationStateView:
    """Run 状态视图。

    作用：从 L2 状态切片与 L3 上下文表达 Run 当前视图。
    边界：不读取外部状态，不刷新投影，不创建真实运行循环。
    """

    view_ref: TypedRef | None = None
    run_ref: RunOrchestrationRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    runtime_slice_projection: RuntimeSliceProjectionState | None = None
    task_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    turn_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    math_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affective_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dynamic_drive_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("RunOrchestrationStateView.missing_state_fields entries must be short")
        if len(self.summary) > 512:
            raise ValueError("RunOrchestrationStateView.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RunOrchestrationStateView.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunContinuityEvaluation:
    """Run 连续性评估事实。"""

    evaluation_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    state_view: RunOrchestrationStateView | None = None
    progress_snapshot: RunProgressSnapshot | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    transition_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("RunContinuityEvaluation.advisory_only must remain true in L3 phase 2")
        if len(self.reason_summary) > 512:
            raise ValueError("RunContinuityEvaluation.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RunContinuityEvaluation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunOrchestrationPlan:
    """Run 编排计划事实。"""

    plan_ref: TypedRef | None = None
    run_ref: RunOrchestrationRef | None = None
    state_view: RunOrchestrationStateView | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    progress_snapshot: RunProgressSnapshot | None = None
    transition_candidates: tuple[LifecycleTransitionCandidate, ...] = field(default_factory=tuple)
    transition_advices: tuple[ProcessStateTransitionAdvice, ...] = field(default_factory=tuple)
    resume_advice: RunResumeAdvice | None = None
    continuity_evaluation_ref: TypedRef | None = None
    future_l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l5_boundary_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l6_service_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_budget_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    quota_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rate_limit_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_pressure_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("RunOrchestrationPlan.advisory_only must remain true in L3 phase 2")
        if len(self.summary) > 512:
            raise ValueError("RunOrchestrationPlan.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RunOrchestrationPlan.schema_version cannot be empty")


def build_run_state_view_from_context(
    context: OrchestrationContext,
    run_ref: RunOrchestrationRef,
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN,
) -> RunOrchestrationStateView:
    """从已传入的 L3 上下文构造 Run 状态视图；不读取外部状态。"""

    missing: tuple[str, ...] = ()
    if context.runtime_slice_projection is None:
        missing = ("runtime_slice_projection",)
    return RunOrchestrationStateView(
        run_ref=run_ref,
        lifecycle=lifecycle,
        runtime_slice_projection=context.runtime_slice_projection,
        math_state_refs=context.math_state_refs,
        affective_state_refs=context.affective_state_refs,
        dynamic_drive_refs=context.dynamic_drive_refs,
        boundary_refs=context.boundary_refs,
        missing_state_fields=missing,
        summary="run state view from provided context",
    )
