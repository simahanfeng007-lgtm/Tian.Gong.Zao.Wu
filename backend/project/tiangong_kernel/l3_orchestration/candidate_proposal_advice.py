"""L3 第六阶段候选提议流程纯建议对象。

本模块只表达候选信号、证据引用、审查提示、晋升/拒绝建议与路径排序。
它不自动入库，不自动合入，不生成补丁、Skill、Tool 或知识。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class CandidateProposalKind(str, Enum):
    UNKNOWN = "unknown"
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    LEARNING = "learning"
    AFFECTIVE = "affective"
    CONTEXT = "context"
    OBSERVATION = "observation"


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
class CandidateEvidenceRef:
    evidence_ref: TypedRef
    evidence_kind_hint: str = "future_candidate_evidence"
    source_ref: TypedRef | None = None
    summary: str = ""
    confidence: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "CandidateEvidenceRef.evidence_kind_hint", 128)
        _ensure_short_text(self.summary, "CandidateEvidenceRef.summary")
        _ensure_unit_interval(self.confidence, "CandidateEvidenceRef.confidence")
        _ensure_advisory(self.ref_only, "CandidateEvidenceRef.ref_only")
        if not self.schema_version:
            raise ValueError("CandidateEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateSignalAdvice:
    advice_ref: TypedRef
    candidate_ref: TypedRef
    proposal_kind: CandidateProposalKind = CandidateProposalKind.UNKNOWN
    signal_value_hint: float = 0.0
    evidence_refs: tuple[CandidateEvidenceRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.signal_value_hint, "CandidateSignalAdvice.signal_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateSignalAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "CandidateSignalAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateSignalAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateReviewRequestHint:
    hint_ref: TypedRef
    candidate_ref: TypedRef
    review_scope_hint: str = "future_candidate_review"
    evidence_refs: tuple[CandidateEvidenceRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.review_scope_hint, "CandidateReviewRequestHint.review_scope_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateReviewRequestHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "CandidateReviewRequestHint.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateReviewRequestHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateProposalAdvice:
    advice_ref: TypedRef
    candidate_ref: TypedRef
    proposal_kind: CandidateProposalKind = CandidateProposalKind.UNKNOWN
    signal_advices: tuple[CandidateSignalAdvice, ...] = field(default_factory=tuple)
    review_hints: tuple[CandidateReviewRequestHint, ...] = field(default_factory=tuple)
    evidence_refs: tuple[CandidateEvidenceRef, ...] = field(default_factory=tuple)
    priority_hint: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.priority_hint, "CandidateProposalAdvice.priority_hint")
        _ensure_short_text(self.reason_summary, "CandidateProposalAdvice.reason_summary")
        _ensure_advisory(self.advisory_only, "CandidateProposalAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateProposalAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidatePromotionAdvice:
    advice_ref: TypedRef
    candidate_ref: TypedRef
    promotion_value_hint: float = 0.0
    evidence_refs: tuple[CandidateEvidenceRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.promotion_value_hint, "CandidatePromotionAdvice.promotion_value_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidatePromotionAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "CandidatePromotionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidatePromotionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateRejectAdvice:
    advice_ref: TypedRef
    candidate_ref: TypedRef
    reject_suitability_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.reject_suitability_hint, "CandidateRejectAdvice.reject_suitability_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateRejectAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "CandidateRejectAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateRejectAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateRouteCandidate:
    route_ref: TypedRef
    candidate_ref: TypedRef
    priority_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.priority_score, "CandidateRouteCandidate.priority_score")
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateRouteCandidate.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "CandidateRouteCandidate.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[CandidateRouteCandidate, ...] = field(default_factory=tuple)
    top_candidate_ref: TypedRef | None = None
    alternative_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "CandidateRouteRanking.confidence")
        _ensure_short_text(self.reason_summary, "CandidateRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "CandidateRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateStateTransitionAdvice:
    advice_ref: TypedRef
    candidate_ref: TypedRef
    suggested_status: str = "ready_for_future_candidate_review"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "CandidateStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "CandidateStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "CandidateStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateStateTransitionAdvice.schema_version cannot be empty")


def build_candidate_route_ranking(
    ranking_ref: TypedRef,
    candidates: tuple[CandidateRouteCandidate, ...],
    confidence: float = 0.8,
) -> CandidateRouteRanking:
    ordered = tuple(sorted(candidates, key=lambda item: (-item.priority_score, item.route_ref.ref_id.value)))
    top = ordered[0].candidate_ref if ordered else None
    alternatives = tuple(item.candidate_ref for item in ordered[1:])
    return CandidateRouteRanking(
        ranking_ref=ranking_ref,
        candidates=ordered,
        top_candidate_ref=top,
        alternative_candidate_refs=alternatives,
        confidence=confidence,
        reason_summary="candidate proposal routes are sorted by advisory priority only",
    )
