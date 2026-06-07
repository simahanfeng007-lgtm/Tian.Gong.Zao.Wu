"""L3 第七阶段自我学习、迭代、进化入口纯编排对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class SelfImprovementFlowKind(str, Enum):
    UNKNOWN = "unknown"
    SELF_LEARNING = "self_learning"
    SELF_ITERATION = "self_iteration"
    SELF_EVOLUTION = "self_evolution"
    WAIT_FOR_EVIDENCE = "wait_for_evidence"


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
class SelfImprovementEvidenceRef:
    evidence_ref: TypedRef
    evidence_kind_hint: str = "future_self_improvement_evidence"
    confidence_hint: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "SelfImprovementEvidenceRef.evidence_kind_hint", 128)
        _ensure_unit_interval(self.confidence_hint, "SelfImprovementEvidenceRef.confidence_hint")
        _ensure_advisory(self.ref_only, "SelfImprovementEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementConstraintHint:
    hint_ref: TypedRef
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = "do_not_bypass_boundaries"
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "SelfImprovementConstraintHint.summary")
        _ensure_advisory(self.advisory_only, "SelfImprovementConstraintHint.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementConstraintHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementBoundaryHint:
    hint_ref: TypedRef
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = "future_boundary_review_required"
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "SelfImprovementBoundaryHint.summary")
        _ensure_advisory(self.advisory_only, "SelfImprovementBoundaryHint.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementBoundaryHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementReadinessScore:
    score_ref: TypedRef
    value: float = 0.0
    confidence: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, "SelfImprovementReadinessScore.value")
        _ensure_unit_interval(self.confidence, "SelfImprovementReadinessScore.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, "SelfImprovementReadinessScore.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "SelfImprovementReadinessScore.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementReadinessScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementSignalAdvice:
    advice_ref: TypedRef
    signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    signal_kind_hint: str = "future_self_improvement_signal"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.signal_kind_hint, "SelfImprovementSignalAdvice.signal_kind_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "SelfImprovementSignalAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "SelfImprovementSignalAdvice.confidence")
        _ensure_advisory(self.advisory_only, "SelfImprovementSignalAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementSignalAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementFlowEntryAdvice:
    advice_ref: TypedRef
    flow_kind: SelfImprovementFlowKind = SelfImprovementFlowKind.UNKNOWN
    evidence_refs: tuple[SelfImprovementEvidenceRef, ...] = field(default_factory=tuple)
    constraint_hints: tuple[SelfImprovementConstraintHint, ...] = field(default_factory=tuple)
    boundary_hints: tuple[SelfImprovementBoundaryHint, ...] = field(default_factory=tuple)
    readiness_score: SelfImprovementReadinessScore | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    auto_execute: bool = False
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.auto_execute is not False:
            raise ValueError("SelfImprovementFlowEntryAdvice.auto_execute must remain false")
        for item in self.reason_codes:
            _ensure_short_text(item, "SelfImprovementFlowEntryAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "SelfImprovementFlowEntryAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementFlowEntryAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfLearningFlowEntryAdvice(SelfImprovementFlowEntryAdvice):
    flow_kind: SelfImprovementFlowKind = SelfImprovementFlowKind.SELF_LEARNING


@dataclass(frozen=True, slots=True)
class SelfIterationFlowEntryAdvice(SelfImprovementFlowEntryAdvice):
    flow_kind: SelfImprovementFlowKind = SelfImprovementFlowKind.SELF_ITERATION


@dataclass(frozen=True, slots=True)
class SelfEvolutionFlowEntryAdvice(SelfImprovementFlowEntryAdvice):
    flow_kind: SelfImprovementFlowKind = SelfImprovementFlowKind.SELF_EVOLUTION


@dataclass(frozen=True, slots=True)
class SelfImprovementRouteCandidate:
    route_ref: TypedRef
    flow_kind: SelfImprovementFlowKind = SelfImprovementFlowKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "SelfImprovementRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "SelfImprovementRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("SelfImprovementRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[SelfImprovementRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("SelfImprovementRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "SelfImprovementRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "SelfImprovementRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfImprovementStateTransitionAdvice:
    advice_ref: TypedRef
    flow_entry_ref: TypedRef
    suggested_status: str = "self_improvement_review_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "SelfImprovementStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "SelfImprovementStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "SelfImprovementStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "SelfImprovementStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("SelfImprovementStateTransitionAdvice.schema_version cannot be empty")


def build_self_improvement_route_ranking(ranking_ref: TypedRef, candidates: tuple[SelfImprovementRouteCandidate, ...]) -> SelfImprovementRouteRanking:
    ordered = tuple(sorted(candidates, key=lambda item: (-item.score, item.route_ref.ref_id.value)))
    return SelfImprovementRouteRanking(ranking_ref=ranking_ref, candidates=ordered, top_route_ref=ordered[0].route_ref if ordered else None, reason_summary="self-improvement route ranking is deterministic advice only")
