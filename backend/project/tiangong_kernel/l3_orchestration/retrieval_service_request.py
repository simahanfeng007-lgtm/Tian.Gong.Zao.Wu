"""L3 第六阶段检索服务纯请求与建议对象。

本模块不访问网络，不执行检索，不做向量化增强检索，不访问数据库或向量库。
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
class RetrievalServiceRequestRef:
    request_ref: TypedRef
    source_context_ref: TypedRef | None = None
    retrieval_scope_hint: str = "future_retrieval_service"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.retrieval_scope_hint, "RetrievalServiceRequestRef.retrieval_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("RetrievalServiceRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalQueryHint:
    hint_ref: TypedRef
    query_terms: tuple[str, ...] = field(default_factory=tuple)
    source_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.query_terms + self.reason_codes:
            _ensure_short_text(item, "RetrievalQueryHint short fields", 128)
        _ensure_advisory(self.advisory_only, "RetrievalQueryHint.advisory_only")
        if not self.schema_version:
            raise ValueError("RetrievalQueryHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalScopeHint:
    hint_ref: TypedRef
    scope_names: tuple[str, ...] = field(default_factory=tuple)
    excluded_scope_names: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.scope_names + self.excluded_scope_names + self.reason_codes:
            _ensure_short_text(item, "RetrievalScopeHint short fields", 128)
        _ensure_advisory(self.advisory_only, "RetrievalScopeHint.advisory_only")
        if not self.schema_version:
            raise ValueError("RetrievalScopeHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalPriorityAdvice:
    advice_ref: TypedRef
    request_ref: TypedRef
    priority_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.priority_hint, "RetrievalPriorityAdvice.priority_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "RetrievalPriorityAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RetrievalPriorityAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RetrievalPriorityAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalResultRef:
    result_ref: TypedRef
    request_ref: TypedRef | None = None
    result_kind_hint: str = "future_retrieval_result"
    summary: str = ""
    confidence: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.result_kind_hint, "RetrievalResultRef.result_kind_hint", 128)
        _ensure_short_text(self.summary, "RetrievalResultRef.summary")
        _ensure_unit_interval(self.confidence, "RetrievalResultRef.confidence")
        _ensure_advisory(self.ref_only, "RetrievalResultRef.ref_only")
        if not self.schema_version:
            raise ValueError("RetrievalResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalResultUseAdvice:
    advice_ref: TypedRef
    result_refs: tuple[RetrievalResultRef, ...] = field(default_factory=tuple)
    use_value_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.use_value_hint, "RetrievalResultUseAdvice.use_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "RetrievalResultUseAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RetrievalResultUseAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RetrievalResultUseAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalServiceRequest:
    request_ref: RetrievalServiceRequestRef
    query_hints: tuple[RetrievalQueryHint, ...] = field(default_factory=tuple)
    scope_hints: tuple[RetrievalScopeHint, ...] = field(default_factory=tuple)
    priority_advices: tuple[RetrievalPriorityAdvice, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "RetrievalServiceRequest.reason_summary")
        _ensure_advisory(self.request_only, "RetrievalServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("RetrievalServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalStateTransitionAdvice:
    advice_ref: TypedRef
    request_ref: TypedRef
    suggested_status: str = "ready_for_future_retrieval_service"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "RetrievalStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "RetrievalStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "RetrievalStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "RetrievalStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RetrievalStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalRouteRanking:
    ranking: SubsystemServiceRouteRanking
    retrieval_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.advisory_only, "RetrievalRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("RetrievalRouteRanking.schema_version cannot be empty")


def retrieval_route_candidate(candidate_ref: TypedRef, request_ref: TypedRef, priority_score: float) -> SubsystemServiceRouteCandidate:
    return SubsystemServiceRouteCandidate(
        candidate_ref=candidate_ref,
        service_kind=SubsystemServiceKind.RETRIEVAL,
        target_request_ref=request_ref,
        priority_score=priority_score,
        reason_codes=("retrieval_service_request_advice_only",),
    )
