"""L3 第八阶段总投影对象。

本模块只表达 L3 编排摘要、数学摘要、路径摘要、追踪引用与审计引用投影。
Projection 不写入 L2，不持久化状态，不实现存储或外部动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathScoreVector
from .orchestration_math_result import StateTransitionAdvice


class OrchestrationProjectionKind(str, Enum):
    """L3 投影类别。"""

    UNKNOWN = "unknown"
    STATE_UPDATE_SUGGESTION = "state_update_suggestion"
    SUMMARY = "summary"
    MATH = "math"
    ROUTE = "route"
    TRACE = "trace"
    AUDIT_REF = "audit_ref"


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
class OrchestrationProjectionRef:
    """L3 投影引用。"""

    projection_ref: TypedRef
    projection_kind: OrchestrationProjectionKind = OrchestrationProjectionKind.UNKNOWN
    source_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.projection_kind, OrchestrationProjectionKind):
            raise ValueError("OrchestrationProjectionRef.projection_kind must use OrchestrationProjectionKind")
        if not self.schema_version:
            raise ValueError("OrchestrationProjectionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationStateUpdateSuggestion:
    """L3 → L2 可记录字段建议；只表达建议，不写入 L2。"""

    suggestion_ref: TypedRef
    subject_ref: TypedRef | None = None
    suggested_field_names: tuple[str, ...] = field(default_factory=tuple)
    state_transition_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    no_persistence: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.suggested_field_names + self.reason_codes:
            _ensure_short_text(item, "OrchestrationStateUpdateSuggestion text", 128)
        _ensure_unit_interval(self.confidence, "OrchestrationStateUpdateSuggestion.confidence")
        _ensure_flag(self.advisory_only, "OrchestrationStateUpdateSuggestion.advisory_only")
        _ensure_flag(self.no_persistence, "OrchestrationStateUpdateSuggestion.no_persistence")
        if not self.schema_version:
            raise ValueError("OrchestrationStateUpdateSuggestion.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationSummaryProjection:
    """L3 编排摘要投影。"""

    projection_ref: OrchestrationProjectionRef
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    component_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    confidence: float = 0.0
    projection_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "OrchestrationSummaryProjection.summary")
        _ensure_unit_interval(self.confidence, "OrchestrationSummaryProjection.confidence")
        _ensure_flag(self.projection_only, "OrchestrationSummaryProjection.projection_only")
        if not self.schema_version:
            raise ValueError("OrchestrationSummaryProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationMathProjection:
    """L3 数学结果摘要投影。"""

    projection_ref: OrchestrationProjectionRef
    score_vectors: tuple[MathScoreVector, ...] = field(default_factory=tuple)
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ranking_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recommendation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "OrchestrationMathProjection.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "OrchestrationMathProjection.confidence")
        _ensure_flag(self.advisory_only, "OrchestrationMathProjection.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationMathProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationRouteProjection:
    """L3 路径排序摘要投影。"""

    projection_ref: OrchestrationProjectionRef
    route_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    alternative_route_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _ref, score in self.route_scores:
            _ensure_unit_interval(score, "OrchestrationRouteProjection.route_scores score")
        for item in self.reason_codes:
            _ensure_short_text(item, "OrchestrationRouteProjection.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "OrchestrationRouteProjection.confidence")
        _ensure_flag(self.advisory_only, "OrchestrationRouteProjection.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationRouteProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationTraceProjection:
    """L3 事件与追踪引用投影。"""

    projection_ref: OrchestrationProjectionRef
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    event_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "OrchestrationTraceProjection.summary")
        _ensure_flag(self.ref_only, "OrchestrationTraceProjection.ref_only")
        if not self.schema_version:
            raise ValueError("OrchestrationTraceProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationAuditRefProjection:
    """L3 审计引用投影；只保留未来审计引用，不写审计。"""

    projection_ref: OrchestrationProjectionRef
    audit_ref_hints: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    ref_only: bool = True
    no_audit_write: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "OrchestrationAuditRefProjection.summary")
        _ensure_flag(self.ref_only, "OrchestrationAuditRefProjection.ref_only")
        _ensure_flag(self.no_audit_write, "OrchestrationAuditRefProjection.no_audit_write")
        if not self.schema_version:
            raise ValueError("OrchestrationAuditRefProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationProjection:
    """L3 总投影聚合对象。"""

    projection_ref: OrchestrationProjectionRef
    summary_projection: OrchestrationSummaryProjection | None = None
    math_projection: OrchestrationMathProjection | None = None
    route_projection: OrchestrationRouteProjection | None = None
    trace_projection: OrchestrationTraceProjection | None = None
    audit_ref_projection: OrchestrationAuditRefProjection | None = None
    state_update_suggestions: tuple[OrchestrationStateUpdateSuggestion, ...] = field(default_factory=tuple)
    transition_advices: tuple[StateTransitionAdvice, ...] = field(default_factory=tuple)
    projection_only: bool = True
    no_l2_write: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.projection_only, "OrchestrationProjection.projection_only")
        _ensure_flag(self.no_l2_write, "OrchestrationProjection.no_l2_write")
        if not self.schema_version:
            raise ValueError("OrchestrationProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationProjectionEnvelope:
    """L3 总投影信封。"""

    envelope_ref: TypedRef
    projection: OrchestrationProjection
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consumer_hint: str = "future_l2_state_record"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    projection_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.consumer_hint, "OrchestrationProjectionEnvelope.consumer_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "OrchestrationProjectionEnvelope.reason_codes", 128)
        _ensure_flag(self.projection_only, "OrchestrationProjectionEnvelope.projection_only")
        if not self.schema_version:
            raise ValueError("OrchestrationProjectionEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationProjectionConsistencyReport:
    """L3 投影一致性报告；只表达检查结果，不触发修复动作。"""

    report_ref: TypedRef
    checked_projection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_projection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_projection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    consistency_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "OrchestrationProjectionConsistencyReport.reason_codes", 128)
        _ensure_unit_interval(self.consistency_score, "OrchestrationProjectionConsistencyReport.consistency_score")
        _ensure_flag(self.report_only, "OrchestrationProjectionConsistencyReport.report_only")
        if not self.schema_version:
            raise ValueError("OrchestrationProjectionConsistencyReport.schema_version cannot be empty")
