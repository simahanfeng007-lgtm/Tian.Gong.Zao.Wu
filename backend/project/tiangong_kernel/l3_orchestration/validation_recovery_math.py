"""L3 第七阶段验证、恢复、迭代、进化数学评分对象。

评分只输出建议、排序和原因码；不运行测试、不回滚、不生成补丁、
不自动合入、不实现实验/迭代/进化算法。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .candidate_change_advice import CandidateVerificationRouteRanking
from .experiment_iteration_evolution_flow import (
    EvolutionPressureScore,
    EvolutionRouteRanking,
    EvolutionValueScore,
    ExperimentRouteRanking,
    ExperimentValueScore,
    IterationNeedScore,
    IterationRouteRanking,
    IterationValueScore,
)
from .observation_context_math import CandidatePriorityScore as ObservationCandidatePriorityScore
from .observation_context_math import ObservationContextSubsystemRouteRanking
from .orchestration_continuity import ContinuityEvaluationSet, RecoveryPriorityScore
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathConstraintSet, MathObjectiveVector, MathScoreVector, ScoreDirection
from .orchestration_math_input import AffectiveWeightInput, DynamicDriveInput
from .orchestration_math_result import RecommendationMode
from .recovery_request import RecoveryReadinessScore, ReversibilityScore, RollbackNeedScore, RecoveryRouteRanking
from .self_improvement_flow import SelfImprovementReadinessScore, SelfImprovementRouteRanking
from .validation_request import ValidationReadinessScore, ValidationRouteRanking, ValidationValueScore


class ValidationRecoveryScoreKind(str, Enum):
    VALIDATION_VALUE = "validation_value"
    VALIDATION_READINESS = "validation_readiness"
    RECOVERY_PRIORITY = "recovery_priority"
    RECOVERY_READINESS = "recovery_readiness"
    ROLLBACK_NEED = "rollback_need"
    REVERSIBILITY = "reversibility"


class IterationEvolutionScoreKind(str, Enum):
    EXPERIMENT_VALUE = "experiment_value"
    ITERATION_NEED = "iteration_need"
    ITERATION_VALUE = "iteration_value"
    EVOLUTION_PRESSURE = "evolution_pressure"
    EVOLUTION_VALUE = "evolution_value"
    SELF_IMPROVEMENT_READINESS = "self_improvement_readiness"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return round(value, 6)


@dataclass(frozen=True, slots=True)
class ValidationRecoveryMathInput:
    input_ref: TypedRef
    validation_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recovery_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    execution_failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    objective_vector: MathObjectiveVector | None = None
    constraint_set: MathConstraintSet | None = None
    continuity_evaluation: ContinuityEvaluationSet | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "ValidationRecoveryMathInput.summary")
        _ensure_advisory(self.advisory_only, "ValidationRecoveryMathInput.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationRecoveryMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRecoveryMathResult:
    result_ref: TypedRef
    math_input: ValidationRecoveryMathInput
    score_vector: MathScoreVector
    validation_route_ranking_ref: TypedRef | None = None
    recovery_route_ranking_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "ValidationRecoveryMathResult.confidence")
        _ensure_short_text(self.reason_summary, "ValidationRecoveryMathResult.reason_summary")
        _ensure_advisory(self.advisory_only, "ValidationRecoveryMathResult.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationRecoveryMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRecoveryRouteRanking:
    ranking_ref: TypedRef
    validation_ranking: ValidationRouteRanking | None = None
    recovery_ranking: RecoveryRouteRanking | None = None
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "ValidationRecoveryRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "ValidationRecoveryRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationRecoveryRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRecoveryRecommendation:
    recommendation_ref: TypedRef
    math_result: ValidationRecoveryMathResult
    route_ranking: ValidationRecoveryRouteRanking | None = None
    recommendation_mode: RecommendationMode = RecommendationMode.SUGGEST
    recommended_validation_ref: TypedRef | None = None
    recommended_recovery_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.recommendation_mode is not RecommendationMode.SUGGEST:
            raise ValueError("ValidationRecoveryRecommendation.recommendation_mode must remain SUGGEST")
        for item in self.reason_codes:
            _ensure_short_text(item, "ValidationRecoveryRecommendation.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "ValidationRecoveryRecommendation.confidence")
        _ensure_advisory(self.advisory_only, "ValidationRecoveryRecommendation.advisory_only")
        if not self.schema_version:
            raise ValueError("ValidationRecoveryRecommendation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationEvolutionMathInput:
    input_ref: TypedRef
    experiment_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    iteration_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evolution_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    self_improvement_entry_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    subsystem_route_ranking: ObservationContextSubsystemRouteRanking | None = None
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "IterationEvolutionMathInput.summary")
        _ensure_advisory(self.advisory_only, "IterationEvolutionMathInput.advisory_only")
        if not self.schema_version:
            raise ValueError("IterationEvolutionMathInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationEvolutionMathResult:
    result_ref: TypedRef
    math_input: IterationEvolutionMathInput
    score_vector: MathScoreVector
    experiment_route_ranking_ref: TypedRef | None = None
    iteration_route_ranking_ref: TypedRef | None = None
    evolution_route_ranking_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "IterationEvolutionMathResult.confidence")
        _ensure_short_text(self.reason_summary, "IterationEvolutionMathResult.reason_summary")
        _ensure_advisory(self.advisory_only, "IterationEvolutionMathResult.advisory_only")
        if not self.schema_version:
            raise ValueError("IterationEvolutionMathResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationEvolutionRouteRanking:
    ranking_ref: TypedRef
    experiment_ranking: ExperimentRouteRanking | None = None
    iteration_ranking: IterationRouteRanking | None = None
    evolution_ranking: EvolutionRouteRanking | None = None
    self_improvement_ranking: SelfImprovementRouteRanking | None = None
    candidate_verification_ranking: CandidateVerificationRouteRanking | None = None
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "IterationEvolutionRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "IterationEvolutionRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("IterationEvolutionRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationEvolutionRecommendation:
    recommendation_ref: TypedRef
    math_result: IterationEvolutionMathResult
    route_ranking: IterationEvolutionRouteRanking | None = None
    recommendation_mode: RecommendationMode = RecommendationMode.SUGGEST
    recommended_experiment_ref: TypedRef | None = None
    recommended_iteration_ref: TypedRef | None = None
    recommended_evolution_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.recommendation_mode is not RecommendationMode.SUGGEST:
            raise ValueError("IterationEvolutionRecommendation.recommendation_mode must remain SUGGEST")
        for item in self.reason_codes:
            _ensure_short_text(item, "IterationEvolutionRecommendation.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "IterationEvolutionRecommendation.confidence")
        _ensure_advisory(self.advisory_only, "IterationEvolutionRecommendation.advisory_only")
        if not self.schema_version:
            raise ValueError("IterationEvolutionRecommendation.schema_version cannot be empty")


def _coverage(present_count: int, missing_count: int) -> float:
    total = present_count + missing_count
    if total <= 0:
        return 1.0
    return _clamp(present_count / total)


def build_validation_value_score(score_ref: TypedRef, evidence_count: int, conflict_count: int = 0, confidence: float = 0.8) -> ValidationValueScore:
    value = _clamp(0.5 + min(evidence_count, 3) * 0.15 - min(conflict_count, 3) * 0.12)
    return ValidationValueScore(score_ref=score_ref, value=value, confidence=confidence, reason_codes=("validation value from evidence refs only",))


def build_validation_readiness_score(score_ref: TypedRef, present_count: int, missing_count: int, confidence: float = 0.78) -> ValidationReadinessScore:
    return ValidationReadinessScore(score_ref=score_ref, value=_coverage(present_count, missing_count), confidence=confidence, reason_codes=("validation readiness from field coverage only",))


def build_recovery_flow_priority_score(score_ref: TypedRef, failure_count: int, reversibility_value: float = 0.5, confidence: float = 0.78) -> RecoveryPriorityScore:
    value = _clamp(0.35 + min(failure_count, 3) * 0.18 + reversibility_value * 0.2)
    return RecoveryPriorityScore(score_ref=score_ref, value=value, confidence=confidence, reason_items=("recovery priority from failure refs and reversibility hint only",))


def build_recovery_readiness_score(score_ref: TypedRef, precondition_value: float, confidence: float = 0.76) -> RecoveryReadinessScore:
    return RecoveryReadinessScore(score_ref=score_ref, value=_clamp(precondition_value), confidence=confidence, reason_codes=("recovery readiness from precondition hint only",))


def build_rollback_need_score(score_ref: TypedRef, failure_pressure: float, reversibility_value: float, confidence: float = 0.75) -> RollbackNeedScore:
    value = _clamp(failure_pressure * 0.65 + reversibility_value * 0.25)
    return RollbackNeedScore(score_ref=score_ref, value=value, confidence=confidence, reason_codes=("rollback need from pressure and reversibility hints only",))


def build_reversibility_score(score_ref: TypedRef, reversible_hint: float, impact_hint: float, confidence: float = 0.74) -> ReversibilityScore:
    value = _clamp(reversible_hint * 0.7 + (1.0 - impact_hint) * 0.3)
    return ReversibilityScore(score_ref=score_ref, value=value, confidence=confidence, reason_codes=("reversibility from hints only",))


def build_experiment_value_score(score_ref: TypedRef, learning_signal_value: float, evidence_value: float, confidence: float = 0.76) -> ExperimentValueScore:
    return ExperimentValueScore(score_ref=score_ref, value=_clamp(learning_signal_value * 0.55 + evidence_value * 0.35), confidence=confidence, reason_codes=("experiment value from signal and evidence hints only",))


def build_iteration_need_score(score_ref: TypedRef, candidate_priority: ObservationCandidatePriorityScore, validation_value: ValidationValueScore, confidence: float = 0.76) -> IterationNeedScore:
    value = _clamp(candidate_priority.value * 0.55 + validation_value.value * 0.35)
    return IterationNeedScore(score_ref=score_ref, value=value, confidence=confidence, reason_codes=("iteration need from candidate and validation scores only",))


def build_evolution_pressure_score(score_ref: TypedRef, iteration_need: IterationNeedScore, stability_pressure: float = 0.0, confidence: float = 0.72) -> EvolutionPressureScore:
    value = _clamp(iteration_need.value * 0.45 + stability_pressure * 0.35)
    return EvolutionPressureScore(score_ref=score_ref, value=value, confidence=confidence, reason_codes=("evolution pressure from iteration and stability hints only",))


def build_self_improvement_readiness_score(score_ref: TypedRef, evidence_value: float, boundary_constraint_value: float, confidence: float = 0.72) -> SelfImprovementReadinessScore:
    value = _clamp(evidence_value * 0.55 + boundary_constraint_value * 0.35)
    return SelfImprovementReadinessScore(score_ref=score_ref, value=value, confidence=confidence, reason_codes=("self-improvement readiness from evidence and boundary hints only",))


def build_validation_recovery_score_vector(vector_ref: TypedRef, validation_value: ValidationValueScore, validation_readiness: ValidationReadinessScore, recovery_priority: RecoveryPriorityScore, rollback_need: RollbackNeedScore, reversibility: ReversibilityScore) -> MathScoreVector:
    return MathScoreVector(
        score_ref=vector_ref,
        score_entries=(
            ("validation_value", validation_value.value, ScoreDirection.BENEFIT),
            ("validation_readiness", validation_readiness.value, ScoreDirection.BENEFIT),
            ("recovery_priority", recovery_priority.value, ScoreDirection.BENEFIT),
            ("rollback_need", rollback_need.value, ScoreDirection.COST),
            ("reversibility", reversibility.value, ScoreDirection.BENEFIT),
        ),
        normalized_score=_clamp((validation_value.value + validation_readiness.value + recovery_priority.value + reversibility.value + (1.0 - rollback_need.value)) / 5.0),
        confidence=min(validation_value.confidence, validation_readiness.confidence, recovery_priority.confidence, rollback_need.confidence, reversibility.confidence),
        penalty_total=rollback_need.value,
        bonus_total=validation_value.value + validation_readiness.value + recovery_priority.value + reversibility.value,
        summary="validation recovery score vector is advisory only",
    )


def build_iteration_evolution_score_vector(vector_ref: TypedRef, experiment_value: ExperimentValueScore, iteration_need: IterationNeedScore, evolution_pressure: EvolutionPressureScore, self_improvement_readiness: SelfImprovementReadinessScore) -> MathScoreVector:
    return MathScoreVector(
        score_ref=vector_ref,
        score_entries=(
            ("experiment_value", experiment_value.value, ScoreDirection.BENEFIT),
            ("iteration_need", iteration_need.value, ScoreDirection.BENEFIT),
            ("evolution_pressure", evolution_pressure.value, ScoreDirection.NEUTRAL),
            ("self_improvement_readiness", self_improvement_readiness.value, ScoreDirection.BENEFIT),
        ),
        normalized_score=_clamp((experiment_value.value + iteration_need.value + evolution_pressure.value + self_improvement_readiness.value) / 4.0),
        confidence=min(experiment_value.confidence, iteration_need.confidence, evolution_pressure.confidence, self_improvement_readiness.confidence),
        bonus_total=experiment_value.value + iteration_need.value + evolution_pressure.value + self_improvement_readiness.value,
        summary="iteration evolution score vector is advisory only",
    )
