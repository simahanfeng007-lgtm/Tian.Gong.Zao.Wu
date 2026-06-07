"""L3 第七阶段实验、迭代、进化流程纯编排对象。

本模块只描述未来实验、迭代、进化流程请求和排序建议，
不运行实验、不生成变更、不扩大边界。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class ExperimentFlowKind(str, Enum):
    UNKNOWN = "unknown"
    REQUEST_DESIGN_REVIEW = "request_design_review"
    REQUEST_EVIDENCE_REVIEW = "request_evidence_review"
    WAIT_FOR_VALIDATION = "wait_for_validation"
    FALLBACK_TO_ITERATION_REVIEW = "fallback_to_iteration_review"


class IterationFlowKind(str, Enum):
    UNKNOWN = "unknown"
    REQUEST_CANDIDATE_REVIEW = "request_candidate_review"
    REQUEST_CHANGE_REVIEW = "request_change_review"
    WAIT_FOR_VALIDATION = "wait_for_validation"
    FALLBACK_TO_EXPERIMENT = "fallback_to_experiment"


class EvolutionFlowKind(str, Enum):
    UNKNOWN = "unknown"
    REQUEST_EVOLUTION_REVIEW = "request_evolution_review"
    REQUEST_BOUNDARY_REVIEW = "request_boundary_review"
    WAIT_FOR_STABILITY_EVIDENCE = "wait_for_stability_evidence"
    FALLBACK_TO_ITERATION = "fallback_to_iteration"


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
class FlowScoreBase:
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
class ExperimentValueScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class ExperimentReadinessScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class IterationNeedScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class IterationValueScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class IterationReadinessScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class EvolutionPressureScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class EvolutionValueScore(FlowScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class ExperimentFlowRequestRef:
    request_ref: TypedRef
    source_candidate_ref: TypedRef | None = None
    request_kind_hint: str = "future_experiment_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.request_kind_hint, "ExperimentFlowRequestRef.request_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("ExperimentFlowRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentHypothesisRef:
    hypothesis_ref: TypedRef
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "ExperimentHypothesisRef.summary")
        _ensure_advisory(self.ref_only, "ExperimentHypothesisRef.ref_only")
        if not self.schema_version:
            raise ValueError("ExperimentHypothesisRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentEvidenceRef:
    evidence_ref: TypedRef
    evidence_kind_hint: str = "future_experiment_evidence"
    confidence_hint: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "ExperimentEvidenceRef.evidence_kind_hint", 128)
        _ensure_unit_interval(self.confidence_hint, "ExperimentEvidenceRef.confidence_hint")
        _ensure_advisory(self.ref_only, "ExperimentEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("ExperimentEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentDesignHint:
    hint_ref: TypedRef
    hypothesis_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    design_kind_hint: str = "future_experiment_design"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.design_kind_hint, "ExperimentDesignHint.design_kind_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ExperimentDesignHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ExperimentDesignHint.advisory_only")
        if not self.schema_version:
            raise ValueError("ExperimentDesignHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentRiskAwarenessHint:
    hint_ref: TypedRef
    risk_awareness_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.risk_awareness_hint, "ExperimentRiskAwarenessHint.risk_awareness_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "ExperimentRiskAwarenessHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ExperimentRiskAwarenessHint.advisory_only")
        if not self.schema_version:
            raise ValueError("ExperimentRiskAwarenessHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentFlowRequest:
    request_ref: ExperimentFlowRequestRef
    design_hints: tuple[ExperimentDesignHint, ...] = field(default_factory=tuple)
    hypothesis_refs: tuple[ExperimentHypothesisRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[ExperimentEvidenceRef, ...] = field(default_factory=tuple)
    risk_awareness_hints: tuple[ExperimentRiskAwarenessHint, ...] = field(default_factory=tuple)
    value_score: ExperimentValueScore | None = None
    readiness_score: ExperimentReadinessScore | None = None
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.request_only, "ExperimentFlowRequest.request_only")
        if not self.schema_version:
            raise ValueError("ExperimentFlowRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentRouteCandidate:
    route_ref: TypedRef
    route_kind: ExperimentFlowKind = ExperimentFlowKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "ExperimentRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "ExperimentRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("ExperimentRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[ExperimentRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("ExperimentRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "ExperimentRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "ExperimentRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("ExperimentRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentStateTransitionAdvice:
    advice_ref: TypedRef
    experiment_request_ref: TypedRef
    suggested_status: str = "experiment_review_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "ExperimentStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "ExperimentStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ExperimentStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "ExperimentStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ExperimentStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationFlowRequestRef:
    request_ref: TypedRef
    source_candidate_ref: TypedRef | None = None
    request_kind_hint: str = "future_iteration_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.request_kind_hint, "IterationFlowRequestRef.request_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("IterationFlowRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationCandidateRef:
    candidate_ref: TypedRef
    candidate_kind_hint: str = "future_iteration_candidate"
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.candidate_kind_hint, "IterationCandidateRef.candidate_kind_hint", 128)
        _ensure_advisory(self.ref_only, "IterationCandidateRef.ref_only")
        if not self.schema_version:
            raise ValueError("IterationCandidateRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationChangeRef:
    change_ref: TypedRef
    change_kind_hint: str = "future_change_ref"
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.change_kind_hint, "IterationChangeRef.change_kind_hint", 128)
        _ensure_advisory(self.ref_only, "IterationChangeRef.ref_only")
        if not self.schema_version:
            raise ValueError("IterationChangeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationEvidenceRef:
    evidence_ref: TypedRef
    evidence_kind_hint: str = "future_iteration_evidence"
    confidence_hint: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "IterationEvidenceRef.evidence_kind_hint", 128)
        _ensure_unit_interval(self.confidence_hint, "IterationEvidenceRef.confidence_hint")
        _ensure_advisory(self.ref_only, "IterationEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("IterationEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationFlowRequest:
    request_ref: IterationFlowRequestRef
    candidate_refs: tuple[IterationCandidateRef, ...] = field(default_factory=tuple)
    change_refs: tuple[IterationChangeRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[IterationEvidenceRef, ...] = field(default_factory=tuple)
    need_score: IterationNeedScore | None = None
    value_score: IterationValueScore | None = None
    readiness_score: IterationReadinessScore | None = None
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.request_only, "IterationFlowRequest.request_only")
        if not self.schema_version:
            raise ValueError("IterationFlowRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationRouteCandidate:
    route_ref: TypedRef
    route_kind: IterationFlowKind = IterationFlowKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "IterationRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "IterationRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("IterationRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[IterationRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("IterationRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "IterationRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "IterationRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("IterationRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationStateTransitionAdvice:
    advice_ref: TypedRef
    iteration_request_ref: TypedRef
    suggested_status: str = "iteration_review_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "IterationStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "IterationStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "IterationStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "IterationStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("IterationStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionFlowRequestRef:
    request_ref: TypedRef
    source_candidate_ref: TypedRef | None = None
    request_kind_hint: str = "future_evolution_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.request_kind_hint, "EvolutionFlowRequestRef.request_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("EvolutionFlowRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionBoundaryHint:
    hint_ref: TypedRef
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_summary: str = "architecture_boundary_review_only"
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.boundary_summary, "EvolutionBoundaryHint.boundary_summary")
        _ensure_advisory(self.advisory_only, "EvolutionBoundaryHint.advisory_only")
        if not self.schema_version:
            raise ValueError("EvolutionBoundaryHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionConstraintHint:
    hint_ref: TypedRef
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    constraint_summary: str = "no_boundary_override"
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.constraint_summary, "EvolutionConstraintHint.constraint_summary")
        _ensure_advisory(self.advisory_only, "EvolutionConstraintHint.advisory_only")
        if not self.schema_version:
            raise ValueError("EvolutionConstraintHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionCandidateRef:
    candidate_ref: TypedRef
    candidate_kind_hint: str = "future_evolution_candidate"
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.candidate_kind_hint, "EvolutionCandidateRef.candidate_kind_hint", 128)
        _ensure_advisory(self.ref_only, "EvolutionCandidateRef.ref_only")
        if not self.schema_version:
            raise ValueError("EvolutionCandidateRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionEvidenceRef:
    evidence_ref: TypedRef
    evidence_kind_hint: str = "future_evolution_evidence"
    confidence_hint: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "EvolutionEvidenceRef.evidence_kind_hint", 128)
        _ensure_unit_interval(self.confidence_hint, "EvolutionEvidenceRef.confidence_hint")
        _ensure_advisory(self.ref_only, "EvolutionEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("EvolutionEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionFlowRequest:
    request_ref: EvolutionFlowRequestRef
    candidate_refs: tuple[EvolutionCandidateRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvolutionEvidenceRef, ...] = field(default_factory=tuple)
    boundary_hints: tuple[EvolutionBoundaryHint, ...] = field(default_factory=tuple)
    constraint_hints: tuple[EvolutionConstraintHint, ...] = field(default_factory=tuple)
    pressure_score: EvolutionPressureScore | None = None
    value_score: EvolutionValueScore | None = None
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_advisory(self.request_only, "EvolutionFlowRequest.request_only")
        if not self.schema_version:
            raise ValueError("EvolutionFlowRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionRouteCandidate:
    route_ref: TypedRef
    route_kind: EvolutionFlowKind = EvolutionFlowKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "EvolutionRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "EvolutionRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("EvolutionRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[EvolutionRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("EvolutionRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "EvolutionRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "EvolutionRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("EvolutionRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionStateTransitionAdvice:
    advice_ref: TypedRef
    evolution_request_ref: TypedRef
    suggested_status: str = "evolution_review_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "EvolutionStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "EvolutionStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "EvolutionStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "EvolutionStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("EvolutionStateTransitionAdvice.schema_version cannot be empty")


def _rank(candidates):
    return tuple(sorted(candidates, key=lambda item: (-item.score, item.route_ref.ref_id.value)))


def build_experiment_route_ranking(ranking_ref: TypedRef, candidates: tuple[ExperimentRouteCandidate, ...]) -> ExperimentRouteRanking:
    ordered = _rank(candidates)
    return ExperimentRouteRanking(ranking_ref=ranking_ref, candidates=ordered, top_route_ref=ordered[0].route_ref if ordered else None, reason_summary="experiment route ranking is deterministic advice only")


def build_iteration_route_ranking(ranking_ref: TypedRef, candidates: tuple[IterationRouteCandidate, ...]) -> IterationRouteRanking:
    ordered = _rank(candidates)
    return IterationRouteRanking(ranking_ref=ranking_ref, candidates=ordered, top_route_ref=ordered[0].route_ref if ordered else None, reason_summary="iteration route ranking is deterministic advice only")


def build_evolution_route_ranking(ranking_ref: TypedRef, candidates: tuple[EvolutionRouteCandidate, ...]) -> EvolutionRouteRanking:
    ordered = _rank(candidates)
    return EvolutionRouteRanking(ranking_ref=ranking_ref, candidates=ordered, top_route_ref=ordered[0].route_ref if ordered else None, reason_summary="evolution route ranking is deterministic advice only")
