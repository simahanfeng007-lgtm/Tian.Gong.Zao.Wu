"""L3 第六阶段面向未来子系统服务的纯请求对象。

本模块只表达服务请求、结果引用、失败引用、需求提示、路由建议和准备度评分。
它不实现任何真实子系统，不调用插件宿主，不执行服务。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class SubsystemServiceKind(str, Enum):
    UNKNOWN = "unknown"
    OBSERVATION = "observation"
    CONTEXT = "context"
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    LEARNING = "learning"
    AFFECTIVE = "affective"
    CANDIDATE_REVIEW = "candidate_review"


class SubsystemServiceRequestStatus(str, Enum):
    DRAFT = "draft"
    PREPARED = "prepared"
    WAITING_FOR_CONTEXT = "waiting_for_context"
    READY_FOR_FUTURE_SERVICE = "ready_for_future_service"


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
class SubsystemServiceRequestRef:
    request_ref: TypedRef
    service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    source_run_ref: TypedRef | None = None
    source_task_ref: TypedRef | None = None
    source_turn_ref: TypedRef | None = None
    source_step_ref: TypedRef | None = None
    source_observation_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SubsystemServiceRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceRequirementHint:
    hint_ref: TypedRef
    service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    required_field_names: tuple[str, ...] = field(default_factory=tuple)
    related_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.required_field_names + self.reason_codes:
            _ensure_short_text(item, "SubsystemServiceRequirementHint short fields", 128)
        _ensure_short_text(self.summary, "SubsystemServiceRequirementHint.summary")
        _ensure_advisory(self.advisory_only, "SubsystemServiceRequirementHint.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceRequirementHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceRequest:
    request_ref: SubsystemServiceRequestRef
    requirement_hints: tuple[SubsystemServiceRequirementHint, ...] = field(default_factory=tuple)
    input_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    expected_output_hints: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.expected_output_hints:
            _ensure_short_text(item, "SubsystemServiceRequest.expected_output_hints", 128)
        _ensure_short_text(self.reason_summary, "SubsystemServiceRequest.reason_summary")
        _ensure_advisory(self.request_only, "SubsystemServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceEnvelope:
    envelope_ref: TypedRef
    request: SubsystemServiceRequest
    status: SubsystemServiceRequestStatus = SubsystemServiceRequestStatus.DRAFT
    present_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    readiness_hint: float = 0.0
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.present_field_names + self.missing_field_names:
            _ensure_short_text(item, "SubsystemServiceEnvelope field names", 128)
        _ensure_unit_interval(self.readiness_hint, "SubsystemServiceEnvelope.readiness_hint")
        _ensure_short_text(self.reason_summary, "SubsystemServiceEnvelope.reason_summary")
        _ensure_advisory(self.request_only, "SubsystemServiceEnvelope.request_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceAdvice:
    advice_ref: TypedRef
    envelope: SubsystemServiceEnvelope
    suggested_next_service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "SubsystemServiceAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "SubsystemServiceAdvice.confidence")
        _ensure_short_text(self.reason_summary, "SubsystemServiceAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "SubsystemServiceAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceResultRef:
    result_ref: TypedRef
    request_ref: TypedRef | None = None
    service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    summary: str = ""
    confidence: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "SubsystemServiceResultRef.summary")
        _ensure_unit_interval(self.confidence, "SubsystemServiceResultRef.confidence")
        _ensure_advisory(self.ref_only, "SubsystemServiceResultRef.ref_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceFailureRef:
    failure_ref: TypedRef
    request_ref: TypedRef | None = None
    service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    failure_kind_hint: str = "unknown"
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.failure_kind_hint, "SubsystemServiceFailureRef.failure_kind_hint", 128)
        _ensure_short_text(self.summary, "SubsystemServiceFailureRef.summary")
        _ensure_advisory(self.ref_only, "SubsystemServiceFailureRef.ref_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceFailureRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceRouteCandidate:
    candidate_ref: TypedRef
    service_kind: SubsystemServiceKind
    target_request_ref: TypedRef
    priority_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.priority_score, "SubsystemServiceRouteCandidate.priority_score")
        for item in self.reason_codes:
            _ensure_short_text(item, "SubsystemServiceRouteCandidate.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "SubsystemServiceRouteCandidate.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[SubsystemServiceRouteCandidate, ...] = field(default_factory=tuple)
    top_candidate_ref: TypedRef | None = None
    alternative_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "SubsystemServiceRouteRanking.confidence")
        _ensure_short_text(self.reason_summary, "SubsystemServiceRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "SubsystemServiceRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceStateTransitionAdvice:
    advice_ref: TypedRef
    request_ref: TypedRef
    suggested_status: str = "ready_for_future_service"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "SubsystemServiceStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "SubsystemServiceStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "SubsystemServiceStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "SubsystemServiceStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceStateTransitionAdvice.schema_version cannot be empty")


def build_subsystem_service_route_ranking(
    ranking_ref: TypedRef,
    candidates: tuple[SubsystemServiceRouteCandidate, ...],
    confidence: float = 0.8,
) -> SubsystemServiceRouteRanking:
    ordered = tuple(sorted(candidates, key=lambda item: (-item.priority_score, item.candidate_ref.ref_id.value)))
    top = ordered[0].candidate_ref if ordered else None
    alternatives = tuple(item.candidate_ref for item in ordered[1:])
    return SubsystemServiceRouteRanking(
        ranking_ref=ranking_ref,
        candidates=ordered,
        top_candidate_ref=top,
        alternative_candidate_refs=alternatives,
        confidence=confidence,
        reason_summary="service request candidates are sorted by advisory priority only",
    )
