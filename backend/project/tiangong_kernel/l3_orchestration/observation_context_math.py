"""L3 第六阶段观察、上下文、服务请求与候选提议数学评分对象。

评分只用于可信度、上下文价值、服务需要、候选优先级与路径排序建议。
它不调用观察器，不写上下文，不写记忆，不执行检索，不生成 Skill、Tool 或知识。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .affective_service_request import AffectiveServiceRequest
from .candidate_proposal_advice import CandidateProposalAdvice, CandidateRouteCandidate, CandidateRouteRanking, build_candidate_route_ranking
from .context_carryover import ContextCarryoverAdvice, ContextCompressionNeedAdvice, ContextWindowAdvice
from .learning_service_request import LearningServiceRequest
from .memory_service_request import MemoryServiceRequest
from .observation_feedback import ObservationEnvelope
from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathScoreVector, MathVectorKind, ScoreDirection
from .orchestration_math_input import AffectiveWeightInput, DynamicDriveInput, MathOrchestrationInput
from .orchestration_math_result import MathEvaluation, RecommendationMode
from .retrieval_service_request import RetrievalServiceRequest
from .subsystem_service_request import (
    SubsystemServiceEnvelope,
    SubsystemServiceKind,
    SubsystemServiceRouteCandidate,
    SubsystemServiceRouteRanking,
    build_subsystem_service_route_ranking,
)


class ObservationContextScoreKind(str, Enum):
    OBSERVATION_CREDIBILITY = "observation_credibility"
    OBSERVATION_RELEVANCE = "observation_relevance"
    OBSERVATION_COMPLETENESS = "observation_completeness"
    CONTEXT_VALUE = "context_value"
    CONTEXT_CONTINUITY = "context_continuity"
    CONTEXT_COMPRESSION_NEED = "context_compression_need"
    MEMORY_NEED = "memory_need"
    RETRIEVAL_NEED = "retrieval_need"
    LEARNING_SIGNAL_VALUE = "learning_signal_value"
    LEARNING_NEED = "learning_need"
    AFFECTIVE_NEED = "affective_need"
    CANDIDATE_PRIORITY = "candidate_priority"
    CANDIDATE_LEARNING_VALUE = "candidate_learning_value"
    SUBSYSTEM_SERVICE_READINESS = "subsystem_service_readiness"


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
class ObservationContextScoreBase:
    score_ref: TypedRef
    score_kind: ObservationContextScoreKind
    value: float = 0.0
    confidence: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
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
class ObservationCredibilityScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.OBSERVATION_CREDIBILITY
    observation_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ObservationRelevanceScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.OBSERVATION_RELEVANCE
    observation_ref: TypedRef | None = None
    target_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ObservationCompletenessScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.OBSERVATION_COMPLETENESS
    observation_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ContextValueScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.CONTEXT_VALUE
    context_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ContextContinuityScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.CONTEXT_CONTINUITY
    context_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ContextCompressionNeedScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.CONTEXT_COMPRESSION_NEED
    context_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class MemoryNeedScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.MEMORY_NEED
    request_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class RetrievalNeedScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.RETRIEVAL_NEED
    request_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class LearningSignalValueScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.LEARNING_SIGNAL_VALUE
    signal_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class LearningNeedScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.LEARNING_NEED
    request_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class AffectiveNeedScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.AFFECTIVE_NEED
    request_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class CandidatePriorityScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.CANDIDATE_PRIORITY
    candidate_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class CandidateLearningValueScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.CANDIDATE_LEARNING_VALUE
    candidate_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class SubsystemServiceReadinessScore(ObservationContextScoreBase):
    score_kind: ObservationContextScoreKind = ObservationContextScoreKind.SUBSYSTEM_SERVICE_READINESS
    request_ref: TypedRef | None = None
    service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN


@dataclass(frozen=True, slots=True)
class ObservationFeedbackMathInput:
    input_ref: TypedRef
    observation_envelope: ObservationEnvelope | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    math_input: MathOrchestrationInput | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ObservationFeedbackMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationFeedbackMathResult:
    result_ref: TypedRef
    input_value: ObservationFeedbackMathInput | None = None
    credibility_score: ObservationCredibilityScore | None = None
    relevance_score: ObservationRelevanceScore | None = None
    completeness_score: ObservationCompletenessScore | None = None
    score_vector: MathScoreVector | None = None
    evaluation: MathEvaluation | None = None
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "ObservationFeedbackMathResult.confidence")
        _ensure_advisory(self.advisory_only, "ObservationFeedbackMathResult.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationFeedbackMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextCarryoverMathInput:
    input_ref: TypedRef
    carryover_advice: ContextCarryoverAdvice | None = None
    window_advice: ContextWindowAdvice | None = None
    compression_need_advice: ContextCompressionNeedAdvice | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContextCarryoverMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextCarryoverMathResult:
    result_ref: TypedRef
    input_value: ContextCarryoverMathInput | None = None
    context_value_score: ContextValueScore | None = None
    context_continuity_score: ContextContinuityScore | None = None
    compression_need_score: ContextCompressionNeedScore | None = None
    score_vector: MathScoreVector | None = None
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "ContextCarryoverMathResult.confidence")
        _ensure_advisory(self.advisory_only, "ContextCarryoverMathResult.advisory_only")
        if not self.schema_version:
            raise ValueError("ContextCarryoverMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceMathInput:
    input_ref: TypedRef
    service_envelope: SubsystemServiceEnvelope | None = None
    memory_request: MemoryServiceRequest | None = None
    retrieval_request: RetrievalServiceRequest | None = None
    learning_request: LearningServiceRequest | None = None
    affective_request: AffectiveServiceRequest | None = None
    candidate_proposal: CandidateProposalAdvice | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SubsystemServiceMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceMathResult:
    result_ref: TypedRef
    input_value: SubsystemServiceMathInput | None = None
    readiness_score: SubsystemServiceReadinessScore | None = None
    memory_need_score: MemoryNeedScore | None = None
    retrieval_need_score: RetrievalNeedScore | None = None
    learning_need_score: LearningNeedScore | None = None
    affective_need_score: AffectiveNeedScore | None = None
    candidate_priority_score: CandidatePriorityScore | None = None
    score_vector: MathScoreVector | None = None
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "SubsystemServiceMathResult.confidence")
        _ensure_advisory(self.advisory_only, "SubsystemServiceMathResult.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationContextSubsystemRouteRanking:
    ranking_ref: TypedRef
    observation_route_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    context_route_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    subsystem_route_ranking: SubsystemServiceRouteRanking | None = None
    candidate_route_ranking: CandidateRouteRanking | None = None
    top_target_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "ObservationContextSubsystemRouteRanking.confidence")
        _ensure_short_text(self.reason_summary, "ObservationContextSubsystemRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "ObservationContextSubsystemRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("ObservationContextSubsystemRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SubsystemServiceRecommendation:
    recommendation_ref: TypedRef
    math_result: SubsystemServiceMathResult | None = None
    route_ranking: ObservationContextSubsystemRouteRanking | None = None
    recommendation_mode: RecommendationMode = RecommendationMode.SUGGEST
    recommended_service_request_ref: TypedRef | None = None
    alternative_service_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.recommendation_mode is not RecommendationMode.SUGGEST:
            raise ValueError("SubsystemServiceRecommendation.recommendation_mode must remain SUGGEST")
        _ensure_unit_interval(self.confidence, "SubsystemServiceRecommendation.confidence")
        _ensure_short_text(self.reason_summary, "SubsystemServiceRecommendation.reason_summary")
        _ensure_advisory(self.advisory_only, "SubsystemServiceRecommendation.advisory_only")
        if not self.schema_version:
            raise ValueError("SubsystemServiceRecommendation.schema_version cannot be empty")


def _coverage_score(present: tuple[str, ...], missing: tuple[str, ...]) -> float:
    total = len(tuple(dict.fromkeys(present + missing)))
    if total == 0:
        return 1.0
    return round(len(tuple(dict.fromkeys(present))) / total, 6)


def build_observation_credibility_score(score_ref: TypedRef, envelope: ObservationEnvelope, confidence: float = 0.82) -> ObservationCredibilityScore:
    trust_values = tuple(hint.trust_level_hint for hint in envelope.trust_hints)
    base = envelope.observation_ref.confidence
    if "high" in trust_values:
        base = max(base, 0.86)
    elif envelope.trust_hints:
        base = max(base, 0.68)
    return ObservationCredibilityScore(
        score_ref=score_ref,
        value=round(min(max(base, 0.0), 1.0), 6),
        confidence=confidence,
        reason_codes=("observation reference confidence only",),
        observation_ref=envelope.observation_ref.observation_ref,
    )


def build_observation_relevance_score(score_ref: TypedRef, envelope: ObservationEnvelope, target_ref: TypedRef | None = None) -> ObservationRelevanceScore:
    target_count = len(tuple(ref for ref in (envelope.run_ref, envelope.task_ref, envelope.turn_ref, envelope.step_ref) if ref is not None))
    value = round(min(0.35 + target_count * 0.15, 1.0), 6)
    return ObservationRelevanceScore(
        score_ref=score_ref,
        value=value,
        confidence=0.78,
        reason_codes=("observation linked orchestration refs only",),
        observation_ref=envelope.observation_ref.observation_ref,
        target_ref=target_ref,
    )


def build_observation_completeness_score(score_ref: TypedRef, envelope: ObservationEnvelope) -> ObservationCompletenessScore:
    return ObservationCompletenessScore(
        score_ref=score_ref,
        value=_coverage_score(envelope.present_field_names, envelope.missing_field_names),
        confidence=0.8,
        reason_codes=("observation field coverage only",),
        observation_ref=envelope.observation_ref.observation_ref,
    )


def build_context_value_score(score_ref: TypedRef, advice: ContextCarryoverAdvice) -> ContextValueScore:
    return ContextValueScore(
        score_ref=score_ref,
        value=advice.value_hint,
        confidence=0.78,
        reason_codes=("context carryover value hint only",),
        context_ref=advice.target_context_ref,
    )


def build_context_continuity_score(score_ref: TypedRef, advice: ContextCarryoverAdvice) -> ContextContinuityScore:
    base = 0.4 + min(len(advice.source_context_refs), 3) * 0.15
    if advice.target_context_ref is not None:
        base += 0.1
    return ContextContinuityScore(
        score_ref=score_ref,
        value=round(min(base, 1.0), 6),
        confidence=0.76,
        reason_codes=("context ref continuity only",),
        context_ref=advice.target_context_ref,
    )


def build_context_compression_need_score(score_ref: TypedRef, window_advice: ContextWindowAdvice) -> ContextCompressionNeedScore:
    value = round(min(max(window_advice.estimated_window_pressure, 0.0), 1.0), 6)
    return ContextCompressionNeedScore(
        score_ref=score_ref,
        value=value,
        confidence=0.76,
        reason_codes=("context window pressure only",),
        context_ref=window_advice.window_ref,
    )


def build_memory_need_score(score_ref: TypedRef, request: MemoryServiceRequest) -> MemoryNeedScore:
    hints = len(request.recall_hints) + len(request.write_suggestions) + len(request.promotion_advices)
    value = round(min(0.25 + hints * 0.18, 1.0), 6)
    return MemoryNeedScore(
        score_ref=score_ref,
        value=value,
        confidence=0.77,
        reason_codes=("memory request hint count only",),
        request_ref=request.request_ref.request_ref,
    )


def build_retrieval_need_score(score_ref: TypedRef, request: RetrievalServiceRequest) -> RetrievalNeedScore:
    hints = len(request.query_hints) + len(request.scope_hints)
    value = round(min(0.2 + hints * 0.22, 1.0), 6)
    return RetrievalNeedScore(
        score_ref=score_ref,
        value=value,
        confidence=0.77,
        reason_codes=("retrieval request hint count only",),
        request_ref=request.request_ref.request_ref,
    )


def build_learning_signal_value_score(score_ref: TypedRef, signal_ref: TypedRef, evidence_count: int, signal_hint: float = 0.0) -> LearningSignalValueScore:
    value = round(min(max(signal_hint, 0.0) * 0.7 + min(evidence_count, 3) * 0.1, 1.0), 6)
    return LearningSignalValueScore(
        score_ref=score_ref,
        value=value,
        confidence=0.76,
        reason_codes=("learning signal hint and evidence count only",),
        signal_ref=signal_ref,
    )


def build_learning_need_score(score_ref: TypedRef, request: LearningServiceRequest) -> LearningNeedScore:
    evidence_count = len(request.evidence_refs)
    signal_count = len(request.signal_advices) + len(request.candidate_advices)
    value = round(min(0.18 + evidence_count * 0.12 + signal_count * 0.2, 1.0), 6)
    return LearningNeedScore(
        score_ref=score_ref,
        value=value,
        confidence=0.75,
        reason_codes=("learning request evidence and signal count only",),
        request_ref=request.request_ref.request_ref,
    )


def build_affective_need_score(score_ref: TypedRef, request: AffectiveServiceRequest) -> AffectiveNeedScore:
    hints = len(request.weight_input_refs) + len(request.tendency_advices) + len(request.expression_advices)
    value = round(min(0.15 + hints * 0.18, 1.0), 6)
    return AffectiveNeedScore(
        score_ref=score_ref,
        value=value,
        confidence=0.74,
        reason_codes=("affective request hint count only",),
        request_ref=request.request_ref.request_ref,
    )


def build_candidate_priority_score(
    score_ref: TypedRef,
    proposal: CandidateProposalAdvice,
    affective_input: AffectiveWeightInput | None = None,
    dynamic_drive_input: DynamicDriveInput | None = None,
) -> CandidatePriorityScore:
    base = proposal.priority_hint
    if affective_input is not None:
        base += affective_input.learning_weight * 0.08 + affective_input.persistence_weight * 0.04
    if dynamic_drive_input is not None:
        base += dynamic_drive_input.priority_weight * 0.08
    return CandidatePriorityScore(
        score_ref=score_ref,
        value=round(min(max(base, 0.0), 1.0), 6),
        confidence=0.78,
        reason_codes=("candidate priority hint with tendency weights only",),
        candidate_ref=proposal.candidate_ref,
    )


def build_candidate_learning_value_score(score_ref: TypedRef, proposal: CandidateProposalAdvice) -> CandidateLearningValueScore:
    evidence_score = min(len(proposal.evidence_refs), 3) * 0.12
    signal_score = min(len(proposal.signal_advices), 3) * 0.1
    value = round(min(proposal.priority_hint * 0.5 + evidence_score + signal_score, 1.0), 6)
    return CandidateLearningValueScore(
        score_ref=score_ref,
        value=value,
        confidence=0.75,
        reason_codes=("candidate evidence and signal hints only",),
        candidate_ref=proposal.candidate_ref,
    )


def build_subsystem_service_readiness_score(
    score_ref: TypedRef,
    envelope: SubsystemServiceEnvelope,
    affective_input: AffectiveWeightInput | None = None,
    dynamic_drive_input: DynamicDriveInput | None = None,
) -> SubsystemServiceReadinessScore:
    base = _coverage_score(envelope.present_field_names, envelope.missing_field_names) * 0.8 + envelope.readiness_hint * 0.2
    if affective_input is not None:
        base += affective_input.stability_weight * 0.03
    if dynamic_drive_input is not None:
        base += dynamic_drive_input.priority_weight * 0.04
    return SubsystemServiceReadinessScore(
        score_ref=score_ref,
        value=round(min(max(base, 0.0), 1.0), 6),
        confidence=0.78,
        reason_codes=("service request field coverage and tendency weights only",),
        request_ref=envelope.request.request_ref.request_ref,
        service_kind=envelope.request.request_ref.service_kind,
    )


def build_observation_context_score_vector(vector_ref: TypedRef, scores: tuple[ObservationContextScoreBase, ...]) -> MathScoreVector:
    entries = tuple((score.score_kind.value, score.value, ScoreDirection.BENEFIT) for score in scores)
    normalized = round(sum(score.value for score in scores) / len(scores), 6) if scores else 0.0
    return MathScoreVector(
        score_ref=vector_ref,
        vector_kind=MathVectorKind.SCORE,
        score_entries=entries,
        source_score_refs=tuple(score.score_ref for score in scores),
        normalized_score=normalized,
        confidence=min((score.confidence for score in scores), default=0.0),
        summary="observation/context/subsystem scores are advisory only",
    )


def build_observation_context_subsystem_route_ranking(
    ranking_ref: TypedRef,
    subsystem_candidates: tuple[SubsystemServiceRouteCandidate, ...],
    candidate_routes: tuple[CandidateRouteCandidate, ...] = (),
    confidence: float = 0.8,
) -> ObservationContextSubsystemRouteRanking:
    subsystem_ranking = build_subsystem_service_route_ranking(ranking_ref, subsystem_candidates, confidence=confidence)
    candidate_ranking = build_candidate_route_ranking(ranking_ref, candidate_routes, confidence=confidence) if candidate_routes else None
    top = subsystem_ranking.top_candidate_ref or (candidate_ranking.top_candidate_ref if candidate_ranking else None)
    return ObservationContextSubsystemRouteRanking(
        ranking_ref=ranking_ref,
        subsystem_route_ranking=subsystem_ranking,
        candidate_route_ranking=candidate_ranking,
        top_target_ref=top,
        confidence=confidence,
        reason_summary="observation/context/subsystem routes are sorted as advice only",
    )
