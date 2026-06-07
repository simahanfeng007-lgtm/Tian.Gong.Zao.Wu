"""L3 第六阶段观察回流纯编排对象。

本模块只表达观察结果引用、回流信封、路由建议、可信度提示和冲突建议。
它不采样真实观察，不读取桌面、文件、网络、日志、摄像头或数据库。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .execution_routing_advice import ExecutionFailureRef, ExecutionResultRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class ObservationFeedbackKind(str, Enum):
    """观察回流建议类别。"""

    UNKNOWN = "unknown"
    ROUTE_TO_RUN = "route_to_run"
    ROUTE_TO_TASK = "route_to_task"
    ROUTE_TO_TURN = "route_to_turn"
    ROUTE_TO_STEP = "route_to_step"
    REQUEST_CONTEXT_CARRYOVER = "request_context_carryover"
    REQUEST_SUBSYSTEM_SERVICE = "request_subsystem_service"


class ObservationEnvelopeStatus(str, Enum):
    """观察信封状态；只表示 L3 编排视图。"""

    DRAFT = "draft"
    RECEIVED_REF = "received_ref"
    NEEDS_REVIEW = "needs_review"
    READY_FOR_ROUTING_ADVICE = "ready_for_routing_advice"
    CONFLICTED = "conflicted"


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
class ObservationResultRef:
    """观察结果引用；不读取观察内容。"""

    observation_ref: TypedRef
    source_execution_result_ref: ExecutionResultRef | None = None
    source_execution_failure_ref: ExecutionFailureRef | None = None
    observation_kind_hint: str = "unknown"
    summary: str = ""
    confidence: float = 0.0
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.observation_kind_hint, "ObservationResultRef.observation_kind_hint", 128)
        _ensure_short_text(self.summary, "ObservationResultRef.summary")
        _ensure_unit_interval(self.confidence, "ObservationResultRef.confidence")
        if not self.schema_version:
            raise ValueError("ObservationResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationTrustHint:
    """观察可信提示；不做真实验证。"""

    hint_ref: TypedRef
    observation_ref: TypedRef
    trust_basis_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_level_hint: str = "unknown"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.trust_level_hint, "ObservationTrustHint.trust_level_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ObservationTrustHint.reason_codes", 128)
        _ensure_short_text(self.summary, "ObservationTrustHint.summary")
        _ensure_advisory(self.advisory_only, "ObservationTrustHint.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationTrustHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationEnvelope:
    """观察结果回流信封；不采样观察。"""

    envelope_ref: TypedRef
    observation_ref: ObservationResultRef
    status: ObservationEnvelopeStatus = ObservationEnvelopeStatus.DRAFT
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    related_execution_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_hints: tuple[ObservationTrustHint, ...] = field(default_factory=tuple)
    present_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.present_field_names + self.missing_field_names:
            _ensure_short_text(item, "ObservationEnvelope field names", 128)
        _ensure_short_text(self.reason_summary, "ObservationEnvelope.reason_summary")
        _ensure_advisory(self.ref_only, "ObservationEnvelope.ref_only")
        if not self.schema_version:
            raise ValueError("ObservationEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationFeedbackAdvice:
    """观察回流建议；不触发服务。"""

    advice_ref: TypedRef
    envelope: ObservationEnvelope
    feedback_kind: ObservationFeedbackKind = ObservationFeedbackKind.UNKNOWN
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "ObservationFeedbackAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ObservationFeedbackAdvice.confidence")
        _ensure_short_text(self.reason_summary, "ObservationFeedbackAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "ObservationFeedbackAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationFeedbackAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationRoutingAdvice:
    """观察路由建议；只排序引用目标。"""

    advice_ref: TypedRef
    observation_ref: TypedRef
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_target_ref: TypedRef | None = None
    alternative_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _target, score in self.target_scores:
            _ensure_unit_interval(score, "ObservationRoutingAdvice.target_scores score")
        for item in self.reason_codes:
            _ensure_short_text(item, "ObservationRoutingAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ObservationRoutingAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ObservationRoutingAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationRoutingAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationConflictAdvice:
    """观察冲突审查建议；不解决真实冲突。"""

    advice_ref: TypedRef
    conflicting_observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    review_hint: str = "manual_or_future_service_review"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.review_hint, "ObservationConflictAdvice.review_hint", 256)
        for item in self.reason_codes:
            _ensure_short_text(item, "ObservationConflictAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ObservationConflictAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ObservationConflictAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationConflictAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationStateTransitionAdvice:
    """观察相关状态转移建议；不写状态。"""

    advice_ref: TypedRef
    observation_ref: TypedRef
    suggested_status: str = "ready_for_feedback"
    target_state_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "ObservationStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ObservationStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ObservationStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ObservationStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationStateTransitionAdvice.schema_version cannot be empty")
