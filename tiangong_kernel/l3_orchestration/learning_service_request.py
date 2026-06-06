"""L3 第六阶段学习服务纯请求与候选建议对象。

本模块不生成真实 Skill、Tool 或知识，不训练模型，不实现学习算法。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .subsystem_service_request import SubsystemServiceKind, SubsystemServiceRouteCandidate, SubsystemServiceRouteRanking


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
class LearningServiceRequestRef:
    request_ref: TypedRef
    source_signal_ref: TypedRef | None = None
    learning_scope_hint: str = "future_learning_service"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.learning_scope_hint, "LearningServiceRequestRef.learning_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("LearningServiceRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningEvidenceRef:
    evidence_ref: TypedRef
    evidence_kind_hint: str = "future_learning_evidence"
    source_observation_ref: TypedRef | None = None
    summary: str = ""
    confidence: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "LearningEvidenceRef.evidence_kind_hint", 128)
        _ensure_short_text(self.summary, "LearningEvidenceRef.summary")
        _ensure_unit_interval(self.confidence, "LearningEvidenceRef.confidence")
        _ensure_advisory(self.ref_only, "LearningEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("LearningEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningSignalAdvice:
    advice_ref: TypedRef
    signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    signal_value_hint: float = 0.0
    evidence_refs: tuple[LearningEvidenceRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.signal_value_hint, "LearningSignalAdvice.signal_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "LearningSignalAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "LearningSignalAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("LearningSignalAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningCandidateAdvice:
    advice_ref: TypedRef
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_value_hint: float = 0.0
    evidence_refs: tuple[LearningEvidenceRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.learning_value_hint, "LearningCandidateAdvice.learning_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "LearningCandidateAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "LearningCandidateAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("LearningCandidateAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningResultRef:
    result_ref: TypedRef
    request_ref: TypedRef | None = None
    result_kind_hint: str = "future_learning_result"
    summary: str = ""
    confidence: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.result_kind_hint, "LearningResultRef.result_kind_hint", 128)
        _ensure_short_text(self.summary, "LearningResultRef.summary")
        _ensure_unit_interval(self.confidence, "LearningResultRef.confidence")
        _ensure_advisory(self.ref_only, "LearningResultRef.ref_only")
        if not self.schema_version:
            raise ValueError("LearningResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningServiceRequest:
    request_ref: LearningServiceRequestRef
    signal_advices: tuple[LearningSignalAdvice, ...] = field(default_factory=tuple)
    candidate_advices: tuple[LearningCandidateAdvice, ...] = field(default_factory=tuple)
    evidence_refs: tuple[LearningEvidenceRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "LearningServiceRequest.reason_summary")
        _ensure_advisory(self.request_only, "LearningServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("LearningServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningStateTransitionAdvice:
    advice_ref: TypedRef
    request_ref: TypedRef
    suggested_status: str = "ready_for_future_learning_service"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "LearningStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "LearningStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "LearningStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "LearningStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("LearningStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningRouteRanking:
    ranking: SubsystemServiceRouteRanking
    learning_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.advisory_only, "LearningRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("LearningRouteRanking.schema_version cannot be empty")


def learning_route_candidate(candidate_ref: TypedRef, request_ref: TypedRef, priority_score: float) -> SubsystemServiceRouteCandidate:
    return SubsystemServiceRouteCandidate(
        candidate_ref=candidate_ref,
        service_kind=SubsystemServiceKind.LEARNING,
        target_request_ref=request_ref,
        priority_score=priority_score,
        reason_codes=("learning_service_request_advice_only",),
    )
