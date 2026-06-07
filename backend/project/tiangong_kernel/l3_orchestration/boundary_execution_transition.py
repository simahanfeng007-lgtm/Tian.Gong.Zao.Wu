"""L3 第五阶段前四阶段到边界/执行请求的接线建议。

本模块只表达引用和建议，不提交 L5、不调用 L4、不写状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .boundary_request import BoundaryCheckRequest
from .boundary_route_advice import BoundaryRouteRanking
from .boundary_review_advice import BoundaryReviewAdvice
from .execution_request import ExecutionDispatchRequest, ExecutionRequest
from .execution_routing_advice import ExecutionRouteRanking
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class BoundaryExecutionTransitionKind(str, Enum):
    """边界/执行接线建议类别。"""

    INTENT_TO_BOUNDARY = "intent_to_boundary"
    INTENT_TO_EXECUTION_PREPARATION = "intent_to_execution_preparation"
    RUN_BOUNDARY = "run_boundary"
    TASK_BOUNDARY = "task_boundary"
    TURN_BOUNDARY = "turn_boundary"
    STEP_BOUNDARY = "step_boundary"
    RUN_EXECUTION = "run_execution"
    TASK_EXECUTION = "task_execution"
    TURN_EXECUTION = "turn_execution"
    STEP_EXECUTION = "step_execution"
    STATE_TRANSITION = "state_transition"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class SkillToolBoundaryContextRef:
    """Skill / ToolGroup 到边界请求的上下文引用。"""

    context_ref: TypedRef
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    intent_ref: TypedRef | None = None
    boundary_request_ref: TypedRef | None = None
    summary: str = ""
    reference_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "SkillToolBoundaryContextRef.summary")
        _ensure_advisory(self.reference_only, "SkillToolBoundaryContextRef.reference_only")
        if not self.schema_version:
            raise ValueError("SkillToolBoundaryContextRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillToolExecutionContextRef:
    """Skill / ToolGroup 到执行请求的上下文引用。"""

    context_ref: TypedRef
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    execution_request_ref: TypedRef | None = None
    summary: str = ""
    reference_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "SkillToolExecutionContextRef.summary")
        _ensure_advisory(self.reference_only, "SkillToolExecutionContextRef.reference_only")
        if not self.schema_version:
            raise ValueError("SkillToolExecutionContextRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentToBoundaryAdvice:
    """意图到未来边界请求的编排建议。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    boundary_request: BoundaryCheckRequest
    boundary_context_refs: tuple[SkillToolBoundaryContextRef, ...] = field(default_factory=tuple)
    boundary_review_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "IntentToBoundaryAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "IntentToBoundaryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("IntentToBoundaryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentToExecutionPreparationAdvice:
    """意图到未来执行请求准备的编排建议。"""

    advice_ref: TypedRef
    intent_ref: TypedRef
    execution_request: ExecutionRequest
    execution_context_refs: tuple[SkillToolExecutionContextRef, ...] = field(default_factory=tuple)
    boundary_request_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "IntentToExecutionPreparationAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "IntentToExecutionPreparationAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("IntentToExecutionPreparationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunBoundaryAdvice:
    advice_ref: TypedRef
    run_ref: TypedRef
    boundary_route_ranking: BoundaryRouteRanking
    boundary_review_advice: BoundaryReviewAdvice | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "RunBoundaryAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "RunBoundaryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RunBoundaryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskBoundaryAdvice:
    advice_ref: TypedRef
    task_ref: TypedRef
    boundary_request_ref: TypedRef
    boundary_route_ranking_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TaskBoundaryAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "TaskBoundaryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("TaskBoundaryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnBoundaryAdvice:
    advice_ref: TypedRef
    turn_ref: TypedRef
    boundary_request_ref: TypedRef
    carryover_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TurnBoundaryAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "TurnBoundaryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("TurnBoundaryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepBoundaryAdvice:
    advice_ref: TypedRef
    step_ref: TypedRef
    boundary_request_ref: TypedRef
    preparation_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "StepBoundaryAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "StepBoundaryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("StepBoundaryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunExecutionAdvice:
    advice_ref: TypedRef
    run_ref: TypedRef
    execution_route_ranking: ExecutionRouteRanking
    dispatch_request: ExecutionDispatchRequest | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "RunExecutionAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "RunExecutionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RunExecutionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskExecutionAdvice:
    advice_ref: TypedRef
    task_ref: TypedRef
    execution_request_ref: TypedRef
    execution_route_ranking_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TaskExecutionAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "TaskExecutionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("TaskExecutionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnExecutionAdvice:
    advice_ref: TypedRef
    turn_ref: TypedRef
    execution_request_ref: TypedRef
    carryover_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TurnExecutionAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "TurnExecutionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("TurnExecutionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepExecutionAdvice:
    advice_ref: TypedRef
    step_ref: TypedRef
    execution_request_ref: TypedRef
    precondition_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "StepExecutionAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "StepExecutionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("StepExecutionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryExecutionStateTransitionSuggestion:
    """边界/执行请求状态转移建议；不写入状态。"""

    suggestion_ref: TypedRef
    subject_ref: TypedRef
    transition_kind: BoundaryExecutionTransitionKind = BoundaryExecutionTransitionKind.STATE_TRANSITION
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    related_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "BoundaryExecutionStateTransitionSuggestion.transition_score")
        _ensure_short_text(self.reason_summary, "BoundaryExecutionStateTransitionSuggestion.reason_summary")
        _ensure_advisory(self.advisory_only, "BoundaryExecutionStateTransitionSuggestion.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryExecutionStateTransitionSuggestion.schema_version cannot be empty")
