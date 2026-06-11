"""L3 → L6 子系统层交接接口冻结对象。

本模块只表达未来 L6 子系统请求、引用、准备度摘要和冻结说明。
它不实现观察、记忆、检索、学习、情感、验证、恢复、迭代或进化子系统。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .affective_service_request import AffectiveServiceRequest
from .learning_service_request import LearningServiceRequest
from .memory_service_request import MemoryServiceRequest
from .retrieval_service_request import RetrievalServiceRequest
from .subsystem_service_request import SubsystemServiceRequest, SubsystemServiceResultRef, SubsystemServiceFailureRef
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
class ObservationServiceRequest:
    """未来观察服务请求占位；不采样真实观察。"""

    request_ref: TypedRef
    source_ref: TypedRef | None = None
    observation_scope_hint: str = "future_observation_service"
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.observation_scope_hint, "ObservationServiceRequest.observation_scope_hint", 128)
        _ensure_flag(self.request_only, "ObservationServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("ObservationServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationServiceRequest:
    """未来验证服务请求占位；不运行验证。"""

    request_ref: TypedRef
    source_ref: TypedRef | None = None
    validation_scope_hint: str = "future_validation_service"
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.validation_scope_hint, "ValidationServiceRequest.validation_scope_hint", 128)
        _ensure_flag(self.request_only, "ValidationServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("ValidationServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryServiceRequest:
    """未来恢复服务请求占位；不执行恢复。"""

    request_ref: TypedRef
    source_ref: TypedRef | None = None
    recovery_scope_hint: str = "future_recovery_service"
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.recovery_scope_hint, "RecoveryServiceRequest.recovery_scope_hint", 128)
        _ensure_flag(self.request_only, "RecoveryServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("RecoveryServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationServiceRequest:
    """未来迭代服务请求占位；不生成或合入变更。"""

    request_ref: TypedRef
    source_ref: TypedRef | None = None
    iteration_scope_hint: str = "future_iteration_service"
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.iteration_scope_hint, "IterationServiceRequest.iteration_scope_hint", 128)
        _ensure_flag(self.request_only, "IterationServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("IterationServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionServiceRequest:
    """未来进化服务请求占位；不实现进化算法。"""

    request_ref: TypedRef
    source_ref: TypedRef | None = None
    evolution_scope_hint: str = "future_evolution_service"
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evolution_scope_hint, "EvolutionServiceRequest.evolution_scope_hint", 128)
        _ensure_flag(self.request_only, "EvolutionServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("EvolutionServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6SubsystemRequestBundle:
    """未来 L6 子系统请求束。"""

    bundle_ref: TypedRef
    subsystem_requests: tuple[SubsystemServiceRequest, ...] = field(default_factory=tuple)
    memory_requests: tuple[MemoryServiceRequest, ...] = field(default_factory=tuple)
    retrieval_requests: tuple[RetrievalServiceRequest, ...] = field(default_factory=tuple)
    learning_requests: tuple[LearningServiceRequest, ...] = field(default_factory=tuple)
    affective_requests: tuple[AffectiveServiceRequest, ...] = field(default_factory=tuple)
    observation_requests: tuple[ObservationServiceRequest, ...] = field(default_factory=tuple)
    validation_requests: tuple[ValidationServiceRequest, ...] = field(default_factory=tuple)
    recovery_requests: tuple[RecoveryServiceRequest, ...] = field(default_factory=tuple)
    iteration_requests: tuple[IterationServiceRequest, ...] = field(default_factory=tuple)
    evolution_requests: tuple[EvolutionServiceRequest, ...] = field(default_factory=tuple)
    bundle_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.bundle_only, "L3ToL6SubsystemRequestBundle.bundle_only")
        if not self.schema_version:
            raise ValueError("L3ToL6SubsystemRequestBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6SubsystemRefBundle:
    """未来 L6 子系统返回引用束。"""

    bundle_ref: TypedRef
    result_refs: tuple[SubsystemServiceResultRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[SubsystemServiceFailureRef, ...] = field(default_factory=tuple)
    request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.ref_only, "L3ToL6SubsystemRefBundle.ref_only")
        if not self.schema_version:
            raise ValueError("L3ToL6SubsystemRefBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6SubsystemReadinessSummary:
    """L6 服务请求准备度摘要；不等同服务执行授权。"""

    summary_ref: TypedRef
    request_bundle_ref: TypedRef | None = None
    readiness_score: float = 0.0
    missing_requirement_hints: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_score, "L3ToL6SubsystemReadinessSummary.readiness_score")
        for item in self.missing_requirement_hints + self.reason_codes:
            _ensure_short_text(item, "L3ToL6SubsystemReadinessSummary text", 128)
        _ensure_flag(self.advisory_only, "L3ToL6SubsystemReadinessSummary.advisory_only")
        if not self.schema_version:
            raise ValueError("L3ToL6SubsystemReadinessSummary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6NonImplementationGuarantee:
    """L3 不实现子系统保证。"""

    guarantee_ref: TypedRef
    guarantee_items: tuple[str, ...] = ("no_memory_service", "no_retrieval_service", "no_learning_service", "no_affective_service")
    confidence: float = 1.0
    guarantee_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.guarantee_items:
            _ensure_short_text(item, "L3ToL6NonImplementationGuarantee.guarantee_items", 128)
        _ensure_unit_interval(self.confidence, "L3ToL6NonImplementationGuarantee.confidence")
        _ensure_flag(self.guarantee_only, "L3ToL6NonImplementationGuarantee.guarantee_only")
        if not self.schema_version:
            raise ValueError("L3ToL6NonImplementationGuarantee.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6ExpectedConsumerNote:
    """未来 L6 消费方说明。"""

    note_ref: TypedRef
    expected_consumer_hint: str = "future_l6_subsystem_layer"
    required_input_hints: tuple[str, ...] = ("SubsystemServiceRequest", "MemoryServiceRequest", "RetrievalServiceRequest", "LearningServiceRequest", "AffectiveServiceRequest")
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.expected_consumer_hint, "L3ToL6ExpectedConsumerNote.expected_consumer_hint", 128)
        for item in self.required_input_hints:
            _ensure_short_text(item, "L3ToL6ExpectedConsumerNote.required_input_hints", 128)
        _ensure_flag(self.note_only, "L3ToL6ExpectedConsumerNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL6ExpectedConsumerNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6InterfaceFreezeNote:
    """L3 → L6 接口冻结说明。"""

    note_ref: TypedRef
    frozen_object_names: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "L3 to L6 interface is request/ref based."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.frozen_object_names:
            _ensure_short_text(item, "L3ToL6InterfaceFreezeNote.frozen_object_names", 128)
        _ensure_short_text(self.summary, "L3ToL6InterfaceFreezeNote.summary")
        _ensure_flag(self.note_only, "L3ToL6InterfaceFreezeNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL6InterfaceFreezeNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6CompatibilityCheckResult:
    """L3 → L6 交接兼容检查结果。"""

    result_ref: TypedRef
    checked_object_names: tuple[str, ...] = field(default_factory=tuple)
    missing_object_names: tuple[str, ...] = field(default_factory=tuple)
    compatibility_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.checked_object_names + self.missing_object_names:
            _ensure_short_text(item, "L3ToL6CompatibilityCheckResult names", 128)
        _ensure_unit_interval(self.compatibility_score, "L3ToL6CompatibilityCheckResult.compatibility_score")
        _ensure_flag(self.report_only, "L3ToL6CompatibilityCheckResult.report_only")
        if not self.schema_version:
            raise ValueError("L3ToL6CompatibilityCheckResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L6PlanningPrerequisiteNote:
    """L6 策划前置说明。"""

    note_ref: TypedRef
    prerequisite_hints: tuple[str, ...] = ("read_l3_subsystem_freeze", "keep_subsystems_outside_l3")
    summary: str = "Future L6 planning must consume service requests without changing L3 boundaries."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.prerequisite_hints:
            _ensure_short_text(item, "L6PlanningPrerequisiteNote.prerequisite_hints", 128)
        _ensure_short_text(self.summary, "L6PlanningPrerequisiteNote.summary")
        _ensure_flag(self.note_only, "L6PlanningPrerequisiteNote.note_only")
        if not self.schema_version:
            raise ValueError("L6PlanningPrerequisiteNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L6SubsystemOpenQuestionNote:
    """L6 子系统开放问题说明。"""

    note_ref: TypedRef
    question_hints: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "Open questions are planning notes only."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.question_hints:
            _ensure_short_text(item, "L6SubsystemOpenQuestionNote.question_hints", 128)
        _ensure_short_text(self.summary, "L6SubsystemOpenQuestionNote.summary")
        _ensure_flag(self.note_only, "L6SubsystemOpenQuestionNote.note_only")
        if not self.schema_version:
            raise ValueError("L6SubsystemOpenQuestionNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL6HandoffEnvelope:
    """L3 → L6 交接信封。"""

    envelope_ref: TypedRef
    request_bundle: L3ToL6SubsystemRequestBundle | None = None
    ref_bundle: L3ToL6SubsystemRefBundle | None = None
    readiness_summary: L3ToL6SubsystemReadinessSummary | None = None
    non_implementation_guarantee: L3ToL6NonImplementationGuarantee | None = None
    expected_consumer_note: L3ToL6ExpectedConsumerNote | None = None
    freeze_note: L3ToL6InterfaceFreezeNote | None = None
    flow_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    handoff_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.handoff_only, "L3ToL6HandoffEnvelope.handoff_only")
        if not self.schema_version:
            raise ValueError("L3ToL6HandoffEnvelope.schema_version cannot be empty")
