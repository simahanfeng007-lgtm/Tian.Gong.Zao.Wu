"""L6 phase3 dynamic mind scoring model declarations.

The formulas here are light, deterministic, and side-effect-free. Scores are
advisory projections; no score is a permit, command, or final decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_score, ensure_no_live_or_sensitive_text, ensure_ref_text, ensure_schema_version, stable_digest


def clamp01(value: float) -> float:
    ensure_score(value, "score factor")
    return max(0.0, min(1.0, float(value)))


def weighted_mean(pairs: tuple[tuple[float, float], ...]) -> float:
    total_weight = sum(max(0.0, weight) for _, weight in pairs)
    if total_weight <= 0:
        return 0.0
    return clamp01(sum(clamp01(value) * max(0.0, weight) for value, weight in pairs) / total_weight)


@dataclass(frozen=True)
class MindScoreBase:
    score_ref: str = "score:l6_mind_score"
    explanation_digest: str = "summary:l6_mind_score"
    score_is_decision: bool = False
    score_is_authorization: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.score_ref, "MindScoreBase.score_ref")
        ensure_no_live_or_sensitive_text(self.explanation_digest, "MindScoreBase.explanation_digest")
        ensure_bool(self.score_is_decision, "MindScoreBase.score_is_decision")
        ensure_bool(self.score_is_authorization, "MindScoreBase.score_is_authorization")
        if self.score_is_decision or self.score_is_authorization:
            raise ValueError("Mind score cannot be decision or authorization")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class BeliefConfidenceScore(MindScoreBase):
    score_ref: str = "score:l6_phase3_belief_confidence"
    source_reliability: float = 0.5
    evidence_strength: float = 0.5
    multi_source_consistency: float = 0.5
    recency_score: float = 0.5
    long_term_belief_consistency: float = 0.5
    user_explicit_alignment: float = 0.5
    tool_result_alignment: float = 0.5
    model_result_alignment: float = 0.5
    counter_evidence_strength: float = 0.0
    pollution_risk: float = 0.0
    revision_required: bool = False

    @property
    def confidence_score(self) -> float:
        positive = weighted_mean(((self.source_reliability, 1.0), (self.evidence_strength, 1.4), (self.multi_source_consistency, 1.2), (self.recency_score, 0.8), (self.long_term_belief_consistency, 0.9), (self.user_explicit_alignment, 1.3), (self.tool_result_alignment, 1.0), (self.model_result_alignment, 0.7)))
        penalty = weighted_mean(((self.counter_evidence_strength, 1.0), (self.pollution_risk, 0.8)))
        return clamp01(positive * (1.0 - 0.55 * penalty))

    @property
    def uncertainty_score(self) -> float:
        return clamp01(1.0 - self.confidence_score + 0.4 * self.counter_evidence_strength)

    @property
    def conflict_score(self) -> float:
        return clamp01(weighted_mean(((self.counter_evidence_strength, 1.2), (1.0 - self.multi_source_consistency, 0.8))))


@dataclass(frozen=True)
class WorldConstraintScore(MindScoreBase):
    score_ref: str = "score:l6_phase3_world_constraint"
    legal_norm_strength: float = 0.5
    user_requirement_strength: float = 0.5
    system_boundary_strength: float = 0.5
    safety_boundary_strength: float = 0.5
    evidence_strength: float = 0.5
    recency_score: float = 0.5
    conflict_score: float = 0.0
    reversibility_score: float = 0.5

    @property
    def world_constraint_score(self) -> float:
        base = weighted_mean(((self.legal_norm_strength, 1.0), (self.user_requirement_strength, 1.2), (self.system_boundary_strength, 1.4), (self.safety_boundary_strength, 1.5), (self.evidence_strength, 1.0), (self.recency_score, 0.7)))
        return clamp01(base * (1.0 - 0.35 * self.conflict_score))

    @property
    def candidate_fact_strength(self) -> float:
        return clamp01(weighted_mean(((self.evidence_strength, 1.3), (self.recency_score, 0.8), (self.reversibility_score, 0.5))) * (1.0 - 0.5 * self.conflict_score))

    @property
    def conflict_warning(self) -> bool:
        return self.conflict_score >= 0.5


@dataclass(frozen=True)
class GoalPriorityScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_goal_priority_model"
    user_explicit_priority: float = 0.5
    urgency_score: float = 0.5
    dependency_blocking_score: float = 0.0
    risk_level: float = 0.0
    budget_pressure: float = 0.0
    context_continuity_score: float = 0.5
    long_term_goal_alignment: float = 0.5
    failure_blocking_score: float = 0.0
    affective_tendency_weight: float = 0.2

    @property
    def priority_score(self) -> float:
        positive = weighted_mean(((self.user_explicit_priority, 1.5), (self.urgency_score, 1.0), (self.dependency_blocking_score, 0.9), (self.context_continuity_score, 0.6), (self.long_term_goal_alignment, 0.8), (self.failure_blocking_score, 0.9), (self.affective_tendency_weight, 0.2)))
        pressure_penalty = weighted_mean(((self.risk_level, 1.0), (self.budget_pressure, 0.8)))
        return clamp01(positive * (1.0 - 0.35 * pressure_penalty))

    @property
    def blocking_level(self) -> float:
        return clamp01(weighted_mean(((self.dependency_blocking_score, 1.0), (self.failure_blocking_score, 1.0), (self.risk_level, 0.5))))


@dataclass(frozen=True)
class AttentionFocusScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_attention_focus_model"
    latest_user_request_weight: float = 0.7
    failure_point_weight: float = 0.0
    high_risk_weight: float = 0.0
    missing_file_weight: float = 0.0
    test_result_weight: float = 0.0
    context_break_weight: float = 0.0
    budget_pressure_weight: float = 0.0
    audit_gap_weight: float = 0.0
    long_term_goal_deviation_weight: float = 0.0

    @property
    def focus_score(self) -> float:
        return weighted_mean(((self.latest_user_request_weight, 1.4), (self.failure_point_weight, 1.1), (self.high_risk_weight, 1.3), (self.missing_file_weight, 0.8), (self.test_result_weight, 0.8), (self.context_break_weight, 1.0), (self.budget_pressure_weight, 0.7), (self.audit_gap_weight, 0.9), (self.long_term_goal_deviation_weight, 0.6)))

    @property
    def attention_shift_suggested(self) -> bool:
        return self.focus_score >= 0.6


@dataclass(frozen=True)
class AffectiveTendencyScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_affective_tendency_model"
    seven_emotions_vector: float = 0.5
    six_desires_vector: float = 0.5
    fatigue_score: float = 0.0
    pressure_score: float = 0.0
    excitement_score: float = 0.5
    recent_success_score: float = 0.5
    recent_failure_score: float = 0.0
    user_interaction_quality: float = 0.5
    risk_pressure_score: float = 0.0
    pollution_risk_score: float = 0.0

    @property
    def expression_intensity(self) -> float:
        return clamp01(weighted_mean(((self.seven_emotions_vector, 1.0), (self.excitement_score, 0.7), (self.user_interaction_quality, 0.6))) * (1.0 - 0.35 * self.pollution_risk_score))

    @property
    def action_tendency_score(self) -> float:
        return clamp01(weighted_mean(((self.six_desires_vector, 1.0), (self.recent_success_score, 0.6), (1.0 - self.fatigue_score, 0.7), (1.0 - self.pressure_score, 0.5))) * (1.0 - 0.4 * self.risk_pressure_score))

    @property
    def degradation_needed(self) -> bool:
        return weighted_mean(((self.fatigue_score, 1.0), (self.pressure_score, 0.8), (self.risk_pressure_score, 0.8), (self.pollution_risk_score, 0.8), (self.recent_failure_score, 0.6))) >= 0.65


@dataclass(frozen=True)
class MemoryPromotionScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_memory_promotion_model"
    user_explicit_confirmation: float = 0.0
    reuse_frequency: float = 0.0
    task_success_relevance: float = 0.5
    long_term_value: float = 0.5
    conflict_risk: float = 0.0
    pollution_risk: float = 0.0
    privacy_risk: float = 0.0
    freshness_score: float = 0.5

    @property
    def promotion_score(self) -> float:
        positive = weighted_mean(((self.user_explicit_confirmation, 1.7), (self.reuse_frequency, 1.0), (self.task_success_relevance, 1.0), (self.long_term_value, 1.2), (self.freshness_score, 0.5)))
        risk = weighted_mean(((self.conflict_risk, 0.8), (self.pollution_risk, 1.0), (self.privacy_risk, 1.2)))
        return clamp01(positive * (1.0 - 0.7 * risk))

    @property
    def safety_filter_required(self) -> bool:
        return max(self.conflict_risk, self.pollution_risk, self.privacy_risk) >= 0.4


@dataclass(frozen=True)
class ForgettingScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_forgetting_model"
    unused_duration: float = 0.0
    expiry_score: float = 0.0
    conflict_with_new_fact: float = 0.0
    pollution_risk: float = 0.0
    redundancy_score: float = 0.0
    user_forget_request: float = 0.0
    privacy_sensitivity: float = 0.0
    protected_memory_level: float = 0.0

    @property
    def forgetting_score(self) -> float:
        positive = weighted_mean(((self.unused_duration, 0.8), (self.expiry_score, 1.0), (self.conflict_with_new_fact, 1.0), (self.pollution_risk, 0.8), (self.redundancy_score, 0.7), (self.user_forget_request, 1.6), (self.privacy_sensitivity, 0.7)))
        return clamp01(positive * (1.0 - self.protected_memory_level))

    @property
    def retention_exception(self) -> bool:
        return self.protected_memory_level >= 0.9


@dataclass(frozen=True)
class SelfReflectionScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_self_reflection_model"
    task_completion_score: float = 0.5
    user_feedback_signal: float = 0.5
    error_count: float = 0.0
    test_result_score: float = 0.5
    rollback_count: float = 0.0
    context_break_score: float = 0.0
    tool_failure_score: float = 0.0
    plan_execution_deviation: float = 0.0

    @property
    def quality_score(self) -> float:
        quality = weighted_mean(((self.task_completion_score, 1.3), (self.user_feedback_signal, 1.0), (self.test_result_score, 1.1)))
        risk = weighted_mean(((self.error_count, 1.0), (self.rollback_count, 0.7), (self.context_break_score, 0.8), (self.tool_failure_score, 0.7), (self.plan_execution_deviation, 0.8)))
        return clamp01(quality * (1.0 - 0.65 * risk))

    @property
    def learning_need_score(self) -> float:
        return clamp01(1.0 - self.quality_score)


@dataclass(frozen=True)
class PollutionRiskScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_pollution_risk_model"
    toxic_content_exposure: float = 0.0
    negative_interaction_density: float = 0.0
    repeated_dark_pattern_exposure: float = 0.0
    value_conflict_score: float = 0.0
    affective_instability_score: float = 0.0
    memory_contamination_score: float = 0.0
    belief_contamination_score: float = 0.0
    source_reliability: float = 0.5
    counterbalancing_positive_signal: float = 0.5
    value_dictatorship: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.value_dictatorship:
            raise ValueError("Pollution risk model cannot become value dictatorship")

    @property
    def pollution_risk_score(self) -> float:
        exposure = weighted_mean(((self.toxic_content_exposure, 1.0), (self.negative_interaction_density, 0.8), (self.repeated_dark_pattern_exposure, 1.1), (self.value_conflict_score, 0.8), (self.affective_instability_score, 0.9), (self.memory_contamination_score, 1.0), (self.belief_contamination_score, 1.0)))
        mitigation = weighted_mean(((self.source_reliability, 0.5), (self.counterbalancing_positive_signal, 0.9)))
        return clamp01(exposure * (1.0 - 0.45 * mitigation))

    @property
    def audit_required(self) -> bool:
        return self.pollution_risk_score >= 0.5


@dataclass(frozen=True)
class MindFusionScoreModel(MindScoreBase):
    score_ref: str = "score:l6_phase3_mind_fusion_model"
    belief_confidence_score: float = 0.5
    world_constraint_score: float = 0.5
    goal_priority_score: float = 0.5
    attention_focus_score: float = 0.5
    affective_tendency_score: float = 0.5
    memory_promotion_score: float = 0.5
    forgetting_score: float = 0.0
    self_reflection_score: float = 0.5
    pollution_risk_score: float = 0.0
    budget_pressure_score: float = 0.0
    risk_score: float = 0.0

    @property
    def weighted_score(self) -> float:
        positive = weighted_mean(((self.belief_confidence_score, 1.0), (self.world_constraint_score, 1.1), (self.goal_priority_score, 0.9), (self.attention_focus_score, 0.8), (self.affective_tendency_score, 0.3), (self.memory_promotion_score, 0.4), (self.self_reflection_score, 0.8)))
        pressure = weighted_mean(((self.pollution_risk_score, 1.0), (self.budget_pressure_score, 0.8), (self.risk_score, 1.1), (self.forgetting_score, 0.3)))
        return clamp01(positive * (1.0 - 0.45 * pressure))

    @property
    def conflict_resolution_score(self) -> float:
        return clamp01(weighted_mean(((1.0 - self.pollution_risk_score, 0.8), (self.belief_confidence_score, 0.6), (self.world_constraint_score, 0.7), (self.self_reflection_score, 0.5))))

    @property
    def uncertainty_score(self) -> float:
        return clamp01(1.0 - self.weighted_score + 0.35 * max(self.pollution_risk_score, self.risk_score))
