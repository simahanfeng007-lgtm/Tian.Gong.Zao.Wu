"""L3 第七阶段验证流程纯编排对象。

本模块只表达验证请求、验证流程建议与结果引用，不运行测试、不读取报告、
不调用模型、工具或外部系统。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class ValidationFlowKind(str, Enum):
    """验证流程建议类型。"""

    UNKNOWN = "unknown"
    REQUEST_REVIEW = "request_review"
    REQUEST_FUTURE_TEST = "request_future_test"
    USE_EXISTING_EVIDENCE = "use_existing_evidence"
    WAIT_FOR_EVIDENCE = "wait_for_evidence"
    FALLBACK_TO_REVIEW = "fallback_to_review"


class ValidationEnvelopeStatus(str, Enum):
    """验证请求信封状态；只供 L3 编排使用。"""

    DRAFT = "draft"
    READY_FOR_ADVICE = "ready_for_advice"
    NEEDS_EVIDENCE = "needs_evidence"
    NEEDS_REVIEW = "needs_review"
    RESULT_REF_RECEIVED = "result_ref_received"


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
class ValidationRequestRef:
    """验证请求引用。"""

    request_ref: TypedRef
    source_ref: TypedRef | None = None
    request_kind_hint: str = "future_validation_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.request_kind_hint, "ValidationRequestRef.request_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("ValidationRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationTargetRef:
    """验证目标引用。"""

    target_ref: TypedRef
    target_kind_hint: str = "unknown"
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.target_kind_hint, "ValidationTargetRef.target_kind_hint", 128)
        _ensure_short_text(self.summary, "ValidationTargetRef.summary")
        if not self.schema_version:
            raise ValueError("ValidationTargetRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationEvidenceRef:
    """验证证据引用；不读取证据内容。"""

    evidence_ref: TypedRef
    evidence_kind_hint: str = "unknown"
    source_ref: TypedRef | None = None
    confidence_hint: float = 0.0
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "ValidationEvidenceRef.evidence_kind_hint", 128)
        _ensure_unit_interval(self.confidence_hint, "ValidationEvidenceRef.confidence_hint")
        _ensure_short_text(self.summary, "ValidationEvidenceRef.summary")
        _ensure_advisory(self.ref_only, "ValidationEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("ValidationEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRequirementHint:
    """验证需求提示；不执行检查。"""

    hint_ref: TypedRef
    required_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_kind_hint: str = "future_review_requirement"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.requirement_kind_hint, "ValidationRequirementHint.requirement_kind_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationRequirementHint.reason_codes", 128)
        _ensure_short_text(self.summary, "ValidationRequirementHint.summary")
        _ensure_advisory(self.advisory_only, "ValidationRequirementHint.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationRequirementHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    """请求未来层处理验证的纯请求对象。"""

    request_ref: ValidationRequestRef
    target_refs: tuple[ValidationTargetRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[ValidationEvidenceRef, ...] = field(default_factory=tuple)
    requirement_hints: tuple[ValidationRequirementHint, ...] = field(default_factory=tuple)
    requested_scope_hint: str = "future_validation_scope"
    present_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.requested_scope_hint, "ValidationRequest.requested_scope_hint", 128)
        for item in self.present_field_names + self.missing_field_names:
            _ensure_short_text(item, "ValidationRequest field names", 128)
        _ensure_short_text(self.reason_summary, "ValidationRequest.reason_summary")
        _ensure_advisory(self.request_only, "ValidationRequest.request_only")
        if not self.schema_version:
            raise ValueError("ValidationRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationEnvelope:
    """验证请求信封；只携带引用和字段状态。"""

    envelope_ref: TypedRef
    request: ValidationRequest
    status: ValidationEnvelopeStatus = ValidationEnvelopeStatus.DRAFT
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    present_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.present_field_names + self.missing_field_names:
            _ensure_short_text(item, "ValidationEnvelope field names", 128)
        _ensure_short_text(self.reason_summary, "ValidationEnvelope.reason_summary")
        _ensure_advisory(self.ref_only, "ValidationEnvelope.ref_only")
        if not self.schema_version:
            raise ValueError("ValidationEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationFlowAdvice:
    """验证流程建议。"""

    advice_ref: TypedRef
    envelope: ValidationEnvelope
    flow_kind: ValidationFlowKind = ValidationFlowKind.UNKNOWN
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationFlowAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationFlowAdvice.confidence")
        _ensure_short_text(self.reason_summary, "ValidationFlowAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "ValidationFlowAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationFlowAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationScoreBase:
    """验证评分基类；只表达建议值。"""

    score_ref: TypedRef
    value: float = 0.0
    confidence: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, f"{self.__class__.__name__}.value")
        _ensure_unit_interval(self.confidence, f"{self.__class__.__name__}.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, f"{self.__class__.__name__}.reason_codes", 128)
        _ensure_advisory(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationReadinessScore(ValidationScoreBase):
    """验证准备度评分。"""


@dataclass(frozen=True, slots=True)
class ValidationValueScore(ValidationScoreBase):
    """验证价值评分。"""


@dataclass(frozen=True, slots=True)
class ValidationStateTransitionAdvice:
    """验证相关状态转移建议。"""

    advice_ref: TypedRef
    validation_request_ref: TypedRef
    suggested_status: str = "validation_advice_ready"
    target_state_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "ValidationStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ValidationStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationResultRef:
    """未来验证结果引用；不读取报告。"""

    result_ref: TypedRef
    validation_request_ref: TypedRef | None = None
    result_kind_hint: str = "future_validation_result"
    confidence_hint: float = 0.0
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.result_kind_hint, "ValidationResultRef.result_kind_hint", 128)
        _ensure_unit_interval(self.confidence_hint, "ValidationResultRef.confidence_hint")
        _ensure_short_text(self.summary, "ValidationResultRef.summary")
        _ensure_advisory(self.ref_only, "ValidationResultRef.ref_only")
        if not self.schema_version:
            raise ValueError("ValidationResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationFailureRef:
    """未来验证失败引用。"""

    failure_ref: TypedRef
    validation_request_ref: TypedRef | None = None
    failure_kind_hint: str = "future_validation_failure"
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.failure_kind_hint, "ValidationFailureRef.failure_kind_hint", 128)
        _ensure_short_text(self.summary, "ValidationFailureRef.summary")
        _ensure_advisory(self.ref_only, "ValidationFailureRef.ref_only")
        if not self.schema_version:
            raise ValueError("ValidationFailureRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationObservationRef:
    """验证相关观察引用。"""

    observation_ref: TypedRef
    result_ref: ValidationResultRef | None = None
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "ValidationObservationRef.summary")
        _ensure_advisory(self.ref_only, "ValidationObservationRef.ref_only")
        if not self.schema_version:
            raise ValueError("ValidationObservationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationConfidenceHint:
    """验证置信提示。"""

    hint_ref: TypedRef
    result_ref: TypedRef
    confidence_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence_hint, "ValidationConfidenceHint.confidence_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationConfidenceHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ValidationConfidenceHint.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationConfidenceHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationConflictAdvice:
    """验证冲突审查建议。"""

    advice_ref: TypedRef
    conflicting_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    review_hint: str = "future_review"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.review_hint, "ValidationConflictAdvice.review_hint", 256)
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationConflictAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationConflictAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ValidationConflictAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationConflictAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRetryAdvice:
    """验证重试路径建议；不执行重试。"""

    advice_ref: TypedRef
    validation_request_ref: TypedRef
    retry_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    retry_only_as_advice: bool = True
    confidence: float = 0.0
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationRetryAdvice.reason_codes", 128)
        _ensure_advisory(self.retry_only_as_advice, "ValidationRetryAdvice.retry_only_as_advice")
        _ensure_unit_interval(self.confidence, "ValidationRetryAdvice.confidence")
        if not self.schema_version:
            raise ValueError("ValidationRetryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationFallbackAdvice:
    """验证兜底路径建议。"""

    advice_ref: TypedRef
    fallback_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationFallbackAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationFallbackAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ValidationFallbackAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationFallbackAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRouteCandidate:
    """验证路径候选。"""

    route_ref: TypedRef
    route_kind: ValidationFlowKind = ValidationFlowKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "ValidationRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("ValidationRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRouteRanking:
    """验证路径排序。"""

    ranking_ref: TypedRef
    candidates: tuple[ValidationRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("ValidationRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "ValidationRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "ValidationRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationResultUseAdvice:
    """验证结果使用建议。"""

    advice_ref: TypedRef
    result_ref: TypedRef
    suggested_use_hint: str = "future_state_review"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_use_hint, "ValidationResultUseAdvice.suggested_use_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationResultUseAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationResultUseAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ValidationResultUseAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationResultUseAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationResultStateTransitionAdvice:
    """验证结果回流状态转移建议。"""

    advice_ref: TypedRef
    result_ref: TypedRef
    suggested_status: str = "validation_result_ref_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "ValidationResultStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationResultStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationResultStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ValidationResultStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationResultStateTransitionAdvice.schema_version cannot be empty")


def build_validation_route_ranking(ranking_ref: TypedRef, candidates: tuple[ValidationRouteCandidate, ...]) -> ValidationRouteRanking:
    ordered = tuple(sorted(candidates, key=lambda item: (-item.score, item.route_ref.ref_id.value)))
    top = ordered[0].route_ref if ordered else None
    return ValidationRouteRanking(
        ranking_ref=ranking_ref,
        candidates=ordered,
        top_route_ref=top,
        reason_summary="validation route ranking is deterministic advice only",
    )
