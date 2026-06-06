"""L3 第六阶段情感服务纯请求与权重接入对象。

本模块只传递权重引用、倾向建议和表达建议，不计算真实情感，不产生执行令。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math_input import AffectiveWeightInput
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
class AffectiveServiceRequestRef:
    request_ref: TypedRef
    source_context_ref: TypedRef | None = None
    affective_scope_hint: str = "future_affective_service"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.affective_scope_hint, "AffectiveServiceRequestRef.affective_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("AffectiveServiceRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveWeightInputRef:
    input_ref: TypedRef
    source_weight_input: AffectiveWeightInput | None = None
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "AffectiveWeightInputRef.summary")
        _ensure_advisory(self.ref_only, "AffectiveWeightInputRef.ref_only")
        if not self.schema_version:
            raise ValueError("AffectiveWeightInputRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveTendencyAdvice:
    advice_ref: TypedRef
    weight_input_ref: TypedRef | None = None
    tendency_kind: str = "context_service_tendency"
    tendency_score_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.tendency_kind, "AffectiveTendencyAdvice.tendency_kind", 128)
        _ensure_unit_interval(self.tendency_score_hint, "AffectiveTendencyAdvice.tendency_score_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "AffectiveTendencyAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "AffectiveTendencyAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("AffectiveTendencyAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveExpressionAdvice:
    advice_ref: TypedRef
    expression_style_hint: str = "neutral"
    directness_hint: float = 0.0
    warmth_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.expression_style_hint, "AffectiveExpressionAdvice.expression_style_hint", 128)
        _ensure_unit_interval(self.directness_hint, "AffectiveExpressionAdvice.directness_hint")
        _ensure_unit_interval(self.warmth_hint, "AffectiveExpressionAdvice.warmth_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "AffectiveExpressionAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "AffectiveExpressionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("AffectiveExpressionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveBehaviorTendencyAdvice:
    advice_ref: TypedRef
    tendency_kind: str = "service_priority_tendency"
    service_kind_hint: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    tendency_score_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.tendency_kind, "AffectiveBehaviorTendencyAdvice.tendency_kind", 128)
        _ensure_unit_interval(self.tendency_score_hint, "AffectiveBehaviorTendencyAdvice.tendency_score_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "AffectiveBehaviorTendencyAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "AffectiveBehaviorTendencyAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("AffectiveBehaviorTendencyAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveWeightAdjustmentHint:
    hint_ref: TypedRef
    weight_input_ref: TypedRef | None = None
    adjustment_scope_hint: str = "future_affective_service_review"
    adjustment_value_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.adjustment_scope_hint, "AffectiveWeightAdjustmentHint.adjustment_scope_hint", 128)
        _ensure_unit_interval(self.adjustment_value_hint, "AffectiveWeightAdjustmentHint.adjustment_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "AffectiveWeightAdjustmentHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "AffectiveWeightAdjustmentHint.advisory_only")
        if not self.schema_version:
            raise ValueError("AffectiveWeightAdjustmentHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveServiceRequest:
    request_ref: AffectiveServiceRequestRef
    weight_input_refs: tuple[AffectiveWeightInputRef, ...] = field(default_factory=tuple)
    tendency_advices: tuple[AffectiveTendencyAdvice, ...] = field(default_factory=tuple)
    expression_advices: tuple[AffectiveExpressionAdvice, ...] = field(default_factory=tuple)
    behavior_tendency_advices: tuple[AffectiveBehaviorTendencyAdvice, ...] = field(default_factory=tuple)
    adjustment_hints: tuple[AffectiveWeightAdjustmentHint, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "AffectiveServiceRequest.reason_summary")
        _ensure_advisory(self.request_only, "AffectiveServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("AffectiveServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveStateTransitionAdvice:
    advice_ref: TypedRef
    request_ref: TypedRef
    suggested_status: str = "ready_for_future_affective_service"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "AffectiveStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "AffectiveStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "AffectiveStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "AffectiveStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("AffectiveStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveRouteRanking:
    ranking: SubsystemServiceRouteRanking
    affective_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.advisory_only, "AffectiveRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("AffectiveRouteRanking.schema_version cannot be empty")


def affective_route_candidate(candidate_ref: TypedRef, request_ref: TypedRef, priority_score: float) -> SubsystemServiceRouteCandidate:
    return SubsystemServiceRouteCandidate(
        candidate_ref=candidate_ref,
        service_kind=SubsystemServiceKind.AFFECTIVE,
        target_request_ref=request_ref,
        priority_score=priority_score,
        reason_codes=("affective_service_request_advice_only",),
    )
