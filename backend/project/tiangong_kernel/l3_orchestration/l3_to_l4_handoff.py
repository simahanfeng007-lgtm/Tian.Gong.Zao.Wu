"""L3 → L4 执行层交接接口冻结对象。

本模块只表达 L3 交给未来 L4 的执行请求、引用束、准备度摘要与冻结说明。
它不调用 L4，不执行模型、工具、文件、网络、终端或桌面动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .execution_request import ExecutionDispatchRequest, ExecutionPlanRef, ExecutionRequest, ExecutionStepRef, ExecutionTokenRef
from .execution_routing_advice import ExecutionCancelRef, ExecutionFailureRef, ExecutionResultRef, ExecutionResumeRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_flag(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class L3ToL4ExecutionRequestBundle:
    """未来 L4 执行请求束；只打包请求对象，不提交执行。"""

    bundle_ref: TypedRef
    execution_requests: tuple[ExecutionRequest, ...] = field(default_factory=tuple)
    dispatch_requests: tuple[ExecutionDispatchRequest, ...] = field(default_factory=tuple)
    request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    bundle_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.bundle_only, "L3ToL4ExecutionRequestBundle.bundle_only")
        if not self.schema_version:
            raise ValueError("L3ToL4ExecutionRequestBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4ExecutionRefBundle:
    """未来 L4 执行引用束。"""

    bundle_ref: TypedRef
    plan_refs: tuple[ExecutionPlanRef, ...] = field(default_factory=tuple)
    step_refs: tuple[ExecutionStepRef, ...] = field(default_factory=tuple)
    token_refs: tuple[ExecutionTokenRef, ...] = field(default_factory=tuple)
    result_refs: tuple[ExecutionResultRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[ExecutionFailureRef, ...] = field(default_factory=tuple)
    resume_refs: tuple[ExecutionResumeRef, ...] = field(default_factory=tuple)
    cancel_refs: tuple[ExecutionCancelRef, ...] = field(default_factory=tuple)
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.ref_only, "L3ToL4ExecutionRefBundle.ref_only")
        if not self.schema_version:
            raise ValueError("L3ToL4ExecutionRefBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4ExecutionReadinessSummary:
    """执行请求准备度摘要；不等同执行授权。"""

    summary_ref: TypedRef
    request_bundle_ref: TypedRef | None = None
    readiness_score: float = 0.0
    missing_requirement_hints: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_score, "L3ToL4ExecutionReadinessSummary.readiness_score")
        for item in self.missing_requirement_hints + self.reason_codes:
            _ensure_short_text(item, "L3ToL4ExecutionReadinessSummary text", 128)
        _ensure_flag(self.advisory_only, "L3ToL4ExecutionReadinessSummary.advisory_only")
        if not self.schema_version:
            raise ValueError("L3ToL4ExecutionReadinessSummary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4ExecutionBoundaryNote:
    """L3/L4 边界说明。"""

    note_ref: TypedRef
    boundary_hints: tuple[str, ...] = ("l3_request_only", "future_l4_executes")
    summary: str = "L3 prepares execution requests; future L4 owns real execution."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.boundary_hints:
            _ensure_short_text(item, "L3ToL4ExecutionBoundaryNote.boundary_hints", 128)
        _ensure_short_text(self.summary, "L3ToL4ExecutionBoundaryNote.summary")
        _ensure_flag(self.note_only, "L3ToL4ExecutionBoundaryNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL4ExecutionBoundaryNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4NonExecutionGuarantee:
    """L3 不执行保证。"""

    guarantee_ref: TypedRef
    guarantee_items: tuple[str, ...] = ("no_model_call", "no_tool_call", "no_external_action")
    confidence: float = 1.0
    guarantee_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.guarantee_items:
            _ensure_short_text(item, "L3ToL4NonExecutionGuarantee.guarantee_items", 128)
        _ensure_unit_interval(self.confidence, "L3ToL4NonExecutionGuarantee.confidence")
        _ensure_flag(self.guarantee_only, "L3ToL4NonExecutionGuarantee.guarantee_only")
        if not self.schema_version:
            raise ValueError("L3ToL4NonExecutionGuarantee.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4ExpectedConsumerNote:
    """未来 L4 消费方说明。"""

    note_ref: TypedRef
    expected_consumer_hint: str = "future_l4_execution_layer"
    required_input_hints: tuple[str, ...] = ("ExecutionRequest", "ExecutionDispatchRequest")
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.expected_consumer_hint, "L3ToL4ExpectedConsumerNote.expected_consumer_hint", 128)
        for item in self.required_input_hints:
            _ensure_short_text(item, "L3ToL4ExpectedConsumerNote.required_input_hints", 128)
        _ensure_flag(self.note_only, "L3ToL4ExpectedConsumerNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL4ExpectedConsumerNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4InterfaceFreezeNote:
    """L3 → L4 接口冻结说明。"""

    note_ref: TypedRef
    frozen_object_names: tuple[str, ...] = field(default_factory=tuple)
    open_question_hints: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "L3 to L4 interface is request/ref based."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.frozen_object_names + self.open_question_hints:
            _ensure_short_text(item, "L3ToL4InterfaceFreezeNote text", 128)
        _ensure_short_text(self.summary, "L3ToL4InterfaceFreezeNote.summary")
        _ensure_flag(self.note_only, "L3ToL4InterfaceFreezeNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL4InterfaceFreezeNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4CompatibilityCheckResult:
    """L3 → L4 交接兼容检查结果。"""

    result_ref: TypedRef
    checked_object_names: tuple[str, ...] = field(default_factory=tuple)
    missing_object_names: tuple[str, ...] = field(default_factory=tuple)
    compatibility_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.checked_object_names + self.missing_object_names:
            _ensure_short_text(item, "L3ToL4CompatibilityCheckResult names", 128)
        _ensure_unit_interval(self.compatibility_score, "L3ToL4CompatibilityCheckResult.compatibility_score")
        _ensure_flag(self.report_only, "L3ToL4CompatibilityCheckResult.report_only")
        if not self.schema_version:
            raise ValueError("L3ToL4CompatibilityCheckResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L4PlanningPrerequisiteNote:
    """L4 策划前置说明。"""

    note_ref: TypedRef
    prerequisite_hints: tuple[str, ...] = ("read_l3_interface_freeze", "keep_l3_request_objects_pure")
    summary: str = "Future L4 planning must consume L3 requests without mutating L3 boundaries."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.prerequisite_hints:
            _ensure_short_text(item, "L4PlanningPrerequisiteNote.prerequisite_hints", 128)
        _ensure_short_text(self.summary, "L4PlanningPrerequisiteNote.summary")
        _ensure_flag(self.note_only, "L4PlanningPrerequisiteNote.note_only")
        if not self.schema_version:
            raise ValueError("L4PlanningPrerequisiteNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL4HandoffEnvelope:
    """L3 → L4 交接信封。"""

    envelope_ref: TypedRef
    request_bundle: L3ToL4ExecutionRequestBundle | None = None
    ref_bundle: L3ToL4ExecutionRefBundle | None = None
    readiness_summary: L3ToL4ExecutionReadinessSummary | None = None
    boundary_note: L3ToL4ExecutionBoundaryNote | None = None
    non_execution_guarantee: L3ToL4NonExecutionGuarantee | None = None
    expected_consumer_note: L3ToL4ExpectedConsumerNote | None = None
    freeze_note: L3ToL4InterfaceFreezeNote | None = None
    flow_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    safety_chain_ref: TypedRef | None = None
    side_effect_governance_chain_ref: TypedRef | None = None
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    handoff_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.handoff_only, "L3ToL4HandoffEnvelope.handoff_only")
        if not self.schema_version:
            raise ValueError("L3ToL4HandoffEnvelope.schema_version cannot be empty")
