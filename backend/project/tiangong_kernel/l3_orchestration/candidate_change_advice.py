"""L3 第七阶段候选变更与证据链纯编排对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class CandidateVerificationRouteKind(str, Enum):
    UNKNOWN = "unknown"
    VALIDATE_FIRST = "validate_first"
    RECOVER_FIRST = "recover_first"
    EXPERIMENT_FIRST = "experiment_first"
    ITERATION_REVIEW = "iteration_review"
    EVOLUTION_REVIEW = "evolution_review"


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
class CandidateChangeRef:
    change_ref: TypedRef
    change_kind_hint: str = "future_candidate_change"
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.change_kind_hint, "CandidateChangeRef.change_kind_hint", 128)
        _ensure_short_text(self.summary, "CandidateChangeRef.summary")
        _ensure_advisory(self.ref_only, "CandidateChangeRef.ref_only")
        if not self.schema_version:
            raise ValueError("CandidateChangeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidatePatchRef:
    patch_ref: TypedRef
    patch_kind_hint: str = "future_patch_ref_only"
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.patch_kind_hint, "CandidatePatchRef.patch_kind_hint", 128)
        _ensure_short_text(self.summary, "CandidatePatchRef.summary")
        _ensure_advisory(self.ref_only, "CandidatePatchRef.ref_only")
        if not self.schema_version:
            raise ValueError("CandidatePatchRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateEvidenceChainRef:
    chain_ref: TypedRef
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence_hint: float = 0.0
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence_hint, "CandidateEvidenceChainRef.confidence_hint")
        _ensure_advisory(self.ref_only, "CandidateEvidenceChainRef.ref_only")
        if not self.schema_version:
            raise ValueError("CandidateEvidenceChainRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateFlowAdviceBase:
    advice_ref: TypedRef
    candidate_change_ref: CandidateChangeRef | None = None
    evidence_chain_ref: CandidateEvidenceChainRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, f"{self.__class__.__name__}.reason_codes", 128)
        _ensure_unit_interval(self.confidence, f"{self.__class__.__name__}.confidence")
        _ensure_advisory(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateValidationAdvice(CandidateFlowAdviceBase):
    pass


@dataclass(frozen=True, slots=True)
class CandidateRecoveryAdvice(CandidateFlowAdviceBase):
    pass


@dataclass(frozen=True, slots=True)
class CandidateExperimentAdvice(CandidateFlowAdviceBase):
    pass


@dataclass(frozen=True, slots=True)
class CandidateIterationAdvice(CandidateFlowAdviceBase):
    pass


@dataclass(frozen=True, slots=True)
class CandidateEvolutionAdvice(CandidateFlowAdviceBase):
    pass


@dataclass(frozen=True, slots=True)
class CandidateVerificationRouteCandidate:
    route_ref: TypedRef
    route_kind: CandidateVerificationRouteKind = CandidateVerificationRouteKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "CandidateVerificationRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateVerificationRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("CandidateVerificationRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateVerificationRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[CandidateVerificationRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("CandidateVerificationRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "CandidateVerificationRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "CandidateVerificationRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateVerificationRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateVerificationStateTransitionAdvice:
    advice_ref: TypedRef
    candidate_change_ref: TypedRef
    suggested_status: str = "candidate_verification_review_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "CandidateVerificationStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "CandidateVerificationStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "CandidateVerificationStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "CandidateVerificationStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("CandidateVerificationStateTransitionAdvice.schema_version cannot be empty")


def build_candidate_verification_route_ranking(ranking_ref: TypedRef, candidates: tuple[CandidateVerificationRouteCandidate, ...]) -> CandidateVerificationRouteRanking:
    ordered = tuple(sorted(candidates, key=lambda item: (-item.score, item.route_ref.ref_id.value)))
    return CandidateVerificationRouteRanking(ranking_ref=ranking_ref, candidates=ordered, top_route_ref=ordered[0].route_ref if ordered else None, reason_summary="candidate verification route ranking is deterministic advice only")
