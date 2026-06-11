"""L3 第五阶段执行请求纯编排对象。

ExecutionRequest / ExecutionDispatchRequest 只是未来 L4 的请求对象，当前模块不调用 L4、不执行工具、不执行动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ActionIntentRef, ToolIntentRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind


class ExecutionRequestKind(str, Enum):
    """执行请求类别；只表示未来请求类型。"""

    EXECUTION = "execution"
    DISPATCH = "dispatch"
    PRECONDITION = "precondition"
    RESULT_REF = "result_ref"
    FAILURE_REF = "failure_ref"


class ExecutionRequestStatus(str, Enum):
    """执行请求编排状态。"""

    DRAFT = "draft"
    PREPARED = "prepared"
    WAITING_FOR_BOUNDARY = "waiting_for_boundary"
    READY_FOR_FUTURE_EXECUTION = "ready_for_future_execution"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_request_only(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class ExecutionPlanRef:
    plan_ref: TypedRef
    source_intent_ref: TypedRef | None = None
    plan_kind_hint: str = "future_l4_plan"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.plan_kind_hint, "ExecutionPlanRef.plan_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("ExecutionPlanRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionStepRef:
    step_ref: TypedRef
    plan_ref: TypedRef | None = None
    step_label: str = "future_execution_step"
    sequence_index: int = 0
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.step_label, "ExecutionStepRef.step_label", 128)
        if self.sequence_index < 0:
            raise ValueError("ExecutionStepRef.sequence_index cannot be negative")
        if not self.schema_version:
            raise ValueError("ExecutionStepRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionTokenRef:
    """未来执行令牌引用占位；不生成真实令牌。"""

    token_ref: TypedRef
    token_scope_hint: str = "future_l4_token_reference_only"
    source_boundary_request_ref: TypedRef | None = None
    reference_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.token_scope_hint, "ExecutionTokenRef.token_scope_hint", 128)
        _ensure_request_only(self.reference_only, "ExecutionTokenRef.reference_only")
        if not self.schema_version:
            raise ValueError("ExecutionTokenRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionPreconditionHint:
    """未来执行前置条件提示；不检查真实环境。"""

    hint_ref: TypedRef
    required_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    satisfied_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    precondition_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.precondition_score, "ExecutionPreconditionHint.precondition_score")
        _ensure_short_text(self.reason_summary, "ExecutionPreconditionHint.reason_summary")
        _ensure_request_only(self.advisory_only, "ExecutionPreconditionHint.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionPreconditionHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionRequestRef:
    """执行请求引用；不触发执行。"""

    request_ref: TypedRef
    action_intent_ref: ActionIntentRef | None = None
    tool_intent_ref: ToolIntentRef | None = None
    boundary_request_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    request_kind: ExecutionRequestKind = ExecutionRequestKind.EXECUTION
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ExecutionRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """面向未来 L4 的执行纯请求对象。"""

    request_ref: ExecutionRequestRef
    execution_plan_ref: ExecutionPlanRef | None = None
    execution_step_refs: tuple[ExecutionStepRef, ...] = field(default_factory=tuple)
    precondition_hint: ExecutionPreconditionHint | None = None
    execution_token_ref: ExecutionTokenRef | None = None
    payload_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.payload_field_names + self.missing_field_names:
            _ensure_short_text(item, "ExecutionRequest field names", 128)
        _ensure_short_text(self.reason_summary, "ExecutionRequest.reason_summary")
        _ensure_request_only(self.request_only, "ExecutionRequest.request_only")
        if not self.schema_version:
            raise ValueError("ExecutionRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionDispatchRequestRef:
    request_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    boundary_request_ref: TypedRef | None = None
    dispatch_scope_hint: str = "future_l4_dispatch_request"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.dispatch_scope_hint, "ExecutionDispatchRequestRef.dispatch_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("ExecutionDispatchRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionDispatchRequest:
    """未来 L4 执行派发纯请求对象；不派发。"""

    request_ref: ExecutionDispatchRequestRef
    execution_request: ExecutionRequest
    dispatch_precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_hint: float = 0.0
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_hint, "ExecutionDispatchRequest.readiness_hint")
        _ensure_short_text(self.reason_summary, "ExecutionDispatchRequest.reason_summary")
        _ensure_request_only(self.request_only, "ExecutionDispatchRequest.request_only")
        if not self.schema_version:
            raise ValueError("ExecutionDispatchRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionStateTransitionAdvice:
    """执行请求状态转移建议；不写入状态、不调用 L4。"""

    advice_ref: TypedRef
    execution_request_ref: TypedRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "ExecutionStateTransitionAdvice.transition_score")
        _ensure_short_text(self.reason_summary, "ExecutionStateTransitionAdvice.reason_summary")
        _ensure_request_only(self.advisory_only, "ExecutionStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionStateTransitionAdvice.schema_version cannot be empty")
