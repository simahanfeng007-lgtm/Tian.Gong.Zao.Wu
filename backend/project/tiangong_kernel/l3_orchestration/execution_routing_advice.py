"""L3 第五阶段执行回流引用与路径建议。

本模块只表达未来 L4 返回结果、失败、取消、恢复、观察、审计的引用和路由建议。
它不采样观察、不写审计、不执行 retry/fallback。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class ExecutionRouteKind(str, Enum):
    """未来执行路径建议类别。"""

    PREPARE_DISPATCH = "prepare_dispatch"
    WAIT_FOR_BOUNDARY = "wait_for_boundary"
    RETRY_PATH = "retry_path"
    FALLBACK_PATH = "fallback_path"
    RESUME_PATH = "resume_path"
    CANCEL_PATH = "cancel_path"
    RESULT_ROUTING = "result_routing"
    FAILURE_ROUTING = "failure_routing"


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
class ExecutionResultRef:
    """未来执行结果引用；不读取结果内容。"""

    result_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    result_kind_hint: str = "future_l4_result"
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.result_kind_hint, "ExecutionResultRef.result_kind_hint", 128)
        _ensure_short_text(self.summary, "ExecutionResultRef.summary")
        if not self.schema_version:
            raise ValueError("ExecutionResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionFailureRef:
    """未来执行失败引用；不执行恢复。"""

    failure_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    failure_kind_hint: str = "future_l4_failure"
    recoverable_hint: bool = False
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.failure_kind_hint, "ExecutionFailureRef.failure_kind_hint", 128)
        _ensure_short_text(self.summary, "ExecutionFailureRef.summary")
        if not self.schema_version:
            raise ValueError("ExecutionFailureRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionResumeRef:
    resume_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    resume_scope_hint: str = "future_l4_resume_reference"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.resume_scope_hint, "ExecutionResumeRef.resume_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("ExecutionResumeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionCancelRef:
    cancel_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    cancel_scope_hint: str = "future_l4_cancel_reference"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.cancel_scope_hint, "ExecutionCancelRef.cancel_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("ExecutionCancelRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionObservationRef:
    observation_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    observation_scope_hint: str = "future_observation_reference"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.observation_scope_hint, "ExecutionObservationRef.observation_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("ExecutionObservationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionAuditRef:
    audit_ref: TypedRef
    execution_request_ref: TypedRef | None = None
    audit_scope_hint: str = "future_audit_reference"
    reference_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.audit_scope_hint, "ExecutionAuditRef.audit_scope_hint", 128)
        _ensure_advisory(self.reference_only, "ExecutionAuditRef.reference_only")
        if not self.schema_version:
            raise ValueError("ExecutionAuditRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionResultRoutingAdvice:
    """未来执行结果回流路由建议；不写状态。"""

    advice_ref: TypedRef
    result_ref: ExecutionResultRef
    suggested_state_update_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[ExecutionObservationRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[ExecutionAuditRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "ExecutionResultRoutingAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "ExecutionResultRoutingAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionResultRoutingAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionFailureRoutingAdvice:
    """未来执行失败回流路由建议；不恢复、不回滚。"""

    advice_ref: TypedRef
    failure_ref: ExecutionFailureRef
    retry_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    fallback_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "ExecutionFailureRoutingAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "ExecutionFailureRoutingAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionFailureRoutingAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionRetryAdvice:
    """未来执行重试路径建议；不执行重试。"""

    advice_ref: TypedRef
    execution_request_ref: TypedRef
    retry_condition_hints: tuple[str, ...] = field(default_factory=tuple)
    retry_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.retry_condition_hints:
            _ensure_short_text(item, "ExecutionRetryAdvice.retry_condition_hints", 128)
        _ensure_unit_interval(self.retry_score, "ExecutionRetryAdvice.retry_score")
        _ensure_short_text(self.reason_summary, "ExecutionRetryAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "ExecutionRetryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionRetryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionFallbackAdvice:
    """未来执行 fallback 路径建议；不执行 fallback。"""

    advice_ref: TypedRef
    execution_request_ref: TypedRef
    fallback_path_hints: tuple[str, ...] = field(default_factory=tuple)
    fallback_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.fallback_path_hints:
            _ensure_short_text(item, "ExecutionFallbackAdvice.fallback_path_hints", 128)
        _ensure_unit_interval(self.fallback_score, "ExecutionFallbackAdvice.fallback_score")
        _ensure_short_text(self.reason_summary, "ExecutionFallbackAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "ExecutionFallbackAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionFallbackAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionRouteCandidate:
    """未来执行路径候选；仅用于排序。"""

    route_ref: TypedRef
    route_kind: ExecutionRouteKind
    execution_request_ref: TypedRef
    readiness_score: float = 0.0
    precondition_score: float = 0.0
    continuity_score: float = 0.0
    reversibility_score: float = 0.0
    boundary_dependency_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("readiness_score", self.readiness_score),
            ("precondition_score", self.precondition_score),
            ("continuity_score", self.continuity_score),
            ("reversibility_score", self.reversibility_score),
            ("boundary_dependency_score", self.boundary_dependency_score),
        ):
            _ensure_unit_interval(value, f"ExecutionRouteCandidate.{name}")
        for item in self.reason_codes:
            _ensure_short_text(item, "ExecutionRouteCandidate.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ExecutionRouteCandidate.advisory_only")
        if not self.schema_version:
            raise ValueError("ExecutionRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionRouteRanking:
    """未来执行路径排序；不是执行调度。"""

    ranking_ref: TypedRef
    candidates: tuple[ExecutionRouteCandidate, ...] = field(default_factory=tuple)
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    ranking_reason: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.ranking_reason, "ExecutionRouteRanking.ranking_reason")
        _ensure_advisory(self.advisory_only, "ExecutionRouteRanking.advisory_only")
        if self.candidates and self.top_route_ref is None:
            raise ValueError("ExecutionRouteRanking.top_route_ref is required when candidates exist")
        if not self.schema_version:
            raise ValueError("ExecutionRouteRanking.schema_version cannot be empty")


def _execution_candidate_score(candidate: ExecutionRouteCandidate) -> float:
    value = (
        candidate.readiness_score * 0.32
        + candidate.precondition_score * 0.24
        + candidate.continuity_score * 0.18
        + candidate.reversibility_score * 0.14
        + candidate.boundary_dependency_score * 0.12
    )
    return round(min(max(value, 0.0), 1.0), 6)


def build_execution_route_ranking(ranking_ref: TypedRef, candidates: tuple[ExecutionRouteCandidate, ...]) -> ExecutionRouteRanking:
    """生成未来执行路径排序；不调用 L4。"""

    scored = tuple((candidate.route_ref, _execution_candidate_score(candidate), candidate) for candidate in candidates)
    ordered = tuple(sorted(scored, key=lambda item: (-item[1], item[0].ref_id.value)))
    return ExecutionRouteRanking(
        ranking_ref=ranking_ref,
        candidates=tuple(item[2] for item in ordered),
        target_scores=tuple((item[0], item[1]) for item in ordered),
        top_route_ref=ordered[0][0] if ordered else None,
        ranking_reason="weighted execution request readiness and precondition completeness",
    )
