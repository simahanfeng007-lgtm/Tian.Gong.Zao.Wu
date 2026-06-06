"""L3 第六阶段记忆服务纯请求与建议对象。

本模块不读取真实记忆，不写入真实记忆，不实现记忆晋升算法。
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
class MemoryServiceRequestRef:
    request_ref: TypedRef
    source_context_ref: TypedRef | None = None
    memory_scope_hint: str = "future_memory_service"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.memory_scope_hint, "MemoryServiceRequestRef.memory_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("MemoryServiceRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryRecallRequestHint:
    hint_ref: TypedRef
    query_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    scope_hint: str = "future_recall_only"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.scope_hint, "MemoryRecallRequestHint.scope_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "MemoryRecallRequestHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "MemoryRecallRequestHint.advisory_only")
        if not self.schema_version:
            raise ValueError("MemoryRecallRequestHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryWriteSuggestion:
    suggestion_ref: TypedRef
    candidate_content_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    write_scope_hint: str = "future_memory_consideration"
    value_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    suggestion_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.write_scope_hint, "MemoryWriteSuggestion.write_scope_hint", 128)
        _ensure_unit_interval(self.value_hint, "MemoryWriteSuggestion.value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "MemoryWriteSuggestion.reason_codes", 128)
        _ensure_advisory(self.suggestion_only, "MemoryWriteSuggestion.suggestion_only")
        if not self.schema_version:
            raise ValueError("MemoryWriteSuggestion.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryPromotionSignalAdvice:
    advice_ref: TypedRef
    memory_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    promotion_value_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.promotion_value_hint, "MemoryPromotionSignalAdvice.promotion_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "MemoryPromotionSignalAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "MemoryPromotionSignalAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("MemoryPromotionSignalAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryConflictReviewAdvice:
    advice_ref: TypedRef
    conflicting_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    review_hint: str = "future_memory_conflict_review"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.review_hint, "MemoryConflictReviewAdvice.review_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "MemoryConflictReviewAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "MemoryConflictReviewAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("MemoryConflictReviewAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryServiceRequest:
    request_ref: MemoryServiceRequestRef
    recall_hints: tuple[MemoryRecallRequestHint, ...] = field(default_factory=tuple)
    write_suggestions: tuple[MemoryWriteSuggestion, ...] = field(default_factory=tuple)
    promotion_advices: tuple[MemoryPromotionSignalAdvice, ...] = field(default_factory=tuple)
    conflict_review_advices: tuple[MemoryConflictReviewAdvice, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "MemoryServiceRequest.reason_summary")
        _ensure_advisory(self.request_only, "MemoryServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("MemoryServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryStateTransitionAdvice:
    advice_ref: TypedRef
    request_ref: TypedRef
    suggested_status: str = "ready_for_future_memory_service"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "MemoryStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "MemoryStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "MemoryStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "MemoryStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("MemoryStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryServiceRouteRanking:
    ranking: SubsystemServiceRouteRanking
    memory_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.advisory_only, "MemoryServiceRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("MemoryServiceRouteRanking.schema_version cannot be empty")


def memory_route_candidate(candidate_ref: TypedRef, request_ref: TypedRef, priority_score: float) -> SubsystemServiceRouteCandidate:
    return SubsystemServiceRouteCandidate(
        candidate_ref=candidate_ref,
        service_kind=SubsystemServiceKind.MEMORY,
        target_request_ref=request_ref,
        priority_score=priority_score,
        reason_codes=("memory_service_request_advice_only",),
    )
