"""L6 phase4 cognitive continuity scoring declarations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_score, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest


def clamp01(value: float) -> float:
    ensure_score(value, "score factor")
    return max(0.0, min(1.0, float(value)))


def weighted_mean(pairs: tuple[tuple[float, float], ...]) -> float:
    total_weight = sum(max(0.0, weight) for _, weight in pairs)
    if total_weight <= 0:
        return 0.0
    return clamp01(sum(clamp01(value) * max(0.0, weight) for value, weight in pairs) / total_weight)


class CognitiveScoreFallbackMode(str, Enum):
    REVIEW_ONLY = "review_only"
    LOW_CONFIDENCE_SUPPRESS_DECISION = "low_confidence_suppress_decision"
    REQUIRE_HUMAN_REVIEW = "require_human_review"


@dataclass(frozen=True)
class ScoreFormulaSpec:
    formula_ref: str = "formula:l6_phase4_score_formula"
    formula_version_ref: str = "formula:l6_phase4_score_formula_v1"
    score_model_ref: str = "score:l6_phase4_score_model"
    score_model_version_ref: str = "score:l6_phase4_score_model_v1"
    weight_profile_ref: str = "weight:l6_phase4_weight_profile"
    weight_profile_version_ref: str = "weight:l6_phase4_weight_profile_v1"
    factor_refs: tuple[str, ...] = field(default_factory=lambda: ("score:l6_phase4_factor",))
    penalty_refs: tuple[str, ...] = field(default_factory=lambda: ("score:l6_phase4_penalty",))
    normalization_policy_ref: str = "policy:l6_phase4_score_normalization"
    confidence_policy_ref: str = "policy:l6_phase4_score_confidence"
    fallback_policy_ref: str = "policy:l6_phase4_score_fallback"
    replay_policy_ref: str = "policy:l6_phase4_score_replay"
    deterministic_formula_ref: str = "formula:l6_phase4_deterministic_formula"
    formula_is_decision: bool = False
    formula_is_authorization: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "formula_ref", "formula_version_ref", "score_model_ref", "score_model_version_ref",
            "weight_profile_ref", "weight_profile_version_ref", "normalization_policy_ref",
            "confidence_policy_ref", "fallback_policy_ref", "replay_policy_ref", "deterministic_formula_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"ScoreFormulaSpec.{field_name}")
        ensure_ref_items(self.factor_refs, "ScoreFormulaSpec.factor_refs", required=True)
        ensure_ref_items(self.penalty_refs, "ScoreFormulaSpec.penalty_refs")
        ensure_bool(self.formula_is_decision, "ScoreFormulaSpec.formula_is_decision")
        ensure_bool(self.formula_is_authorization, "ScoreFormulaSpec.formula_is_authorization")
        if self.formula_is_decision or self.formula_is_authorization:
            raise ValueError("score formula spec cannot become decision or authorization")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True)
class Phase4ScoreBase:
    score_ref: str = "score:l6_phase4_score"
    explanation_digest: str = "summary:l6_phase4_score"
    score_model_ref: str = "score:l6_phase4_score_model"
    score_model_version_ref: str = "score:l6_phase4_score_model_v1"
    formula_ref: str = "formula:l6_phase4_score_formula"
    formula_version_ref: str = "formula:l6_phase4_score_formula_v1"
    weight_profile_ref: str = "weight:l6_phase4_weight_profile"
    weight_profile_version_ref: str = "weight:l6_phase4_weight_profile_v1"
    replay_policy_ref: str = "policy:l6_phase4_score_replay"
    fallback_mode: CognitiveScoreFallbackMode | str = CognitiveScoreFallbackMode.REVIEW_ONLY
    confidence_score: float = 0.9
    score_is_decision: bool = False
    score_is_authorization: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.score_ref, "Phase4ScoreBase.score_ref")
        ensure_no_live_or_sensitive_text(self.explanation_digest, "Phase4ScoreBase.explanation_digest")
        for field_name in ("score_model_ref", "score_model_version_ref", "formula_ref", "formula_version_ref", "weight_profile_ref", "weight_profile_version_ref", "replay_policy_ref"):
            ensure_ref_text(getattr(self, field_name), f"Phase4ScoreBase.{field_name}")
        object.__setattr__(self, "fallback_mode", CognitiveScoreFallbackMode(self.fallback_mode))
        ensure_score(self.confidence_score, "Phase4ScoreBase.confidence_score")
        object.__setattr__(self, "confidence_score", clamp01(self.confidence_score))
        ensure_bool(self.score_is_decision, "Phase4ScoreBase.score_is_decision")
        ensure_bool(self.score_is_authorization, "Phase4ScoreBase.score_is_authorization")
        if self.score_is_decision or self.score_is_authorization:
            raise ValueError("Phase4 scores cannot be decisions or authorizations")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ContextContinuityScore(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_context_continuity"
    conversation_continuity: float = 0.5
    handoff_continuity: float = 0.5
    memory_recall_support: float = 0.5
    context_gap: float = 0.0
    privacy_pressure: float = 0.0

    @property
    def continuity_score(self) -> float:
        base = weighted_mean(((self.conversation_continuity, 1.2), (self.handoff_continuity, 1.0), (self.memory_recall_support, 0.8)))
        risk = weighted_mean(((self.context_gap, 1.0), (self.privacy_pressure, 0.7)))
        return clamp01(base * (1.0 - 0.45 * risk))


@dataclass(frozen=True)
class MemoryReentryScore(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_memory_reentry"
    explicit_user_confirmation: float = 0.0
    reuse_frequency: float = 0.0
    task_relevance: float = 0.5
    long_term_value: float = 0.5
    privacy_risk: float = 0.0
    pollution_risk: float = 0.0
    conflict_risk: float = 0.0

    @property
    def promotion_review_score(self) -> float:
        positive = weighted_mean(((self.explicit_user_confirmation, 1.7), (self.reuse_frequency, 1.0), (self.task_relevance, 1.0), (self.long_term_value, 1.2)))
        risk = weighted_mean(((self.privacy_risk, 1.2), (self.pollution_risk, 1.0), (self.conflict_risk, 0.8)))
        return clamp01(positive * (1.0 - 0.7 * risk))

    @property
    def safety_review_required(self) -> bool:
        return max(self.privacy_risk, self.pollution_risk, self.conflict_risk) >= 0.35


@dataclass(frozen=True)
class ForgettingReviewScore(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_forgetting_review"
    explicit_user_forget_request: float = 0.0
    expiry_pressure: float = 0.0
    conflict_pressure: float = 0.0
    pollution_pressure: float = 0.0
    redundancy_pressure: float = 0.0
    protected_l5_rule_score: float = 0.0

    @property
    def review_score(self) -> float:
        if self.forced_forgetting_review_required:
            return 1.0
        background = weighted_mean(((self.expiry_pressure, 0.8), (self.conflict_pressure, 1.0), (self.pollution_pressure, 0.9), (self.redundancy_pressure, 0.7)))
        positive = clamp01(0.68 * clamp01(self.explicit_user_forget_request) + 0.32 * background)
        return clamp01(positive * (1.0 - self.protected_l5_rule_score))

    @property
    def forced_forgetting_review_required(self) -> bool:
        return clamp01(self.explicit_user_forget_request) >= 0.9

    @property
    def retention_exception_required(self) -> bool:
        return self.protected_l5_rule_score >= 0.9 and not self.forced_forgetting_review_required

    @property
    def l5_retention_conflict_review_required(self) -> bool:
        return self.protected_l5_rule_score >= 0.9 and self.forced_forgetting_review_required


@dataclass(frozen=True)
class CognitiveReentryScore(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_cognitive_reentry"
    context_score: float = 0.5
    memory_score: float = 0.5
    forgetting_score: float = 0.0
    belief_world_score: float = 0.5
    affective_modulation_score: float = 0.5
    pollution_risk_score: float = 0.0
    budget_pressure_score: float = 0.0
    governance_risk_score: float = 0.0

    @property
    def reentry_priority_score(self) -> float:
        positive = weighted_mean(((self.context_score, 1.0), (self.memory_score, 0.8), (self.forgetting_score, 0.7), (self.belief_world_score, 1.0), (self.affective_modulation_score, 0.4)))
        risk = weighted_mean(((self.pollution_risk_score, 1.0), (self.budget_pressure_score, 0.6), (self.governance_risk_score, 1.0)))
        return clamp01(positive * (1.0 - 0.5 * risk))

    @property
    def l5_review_recommended(self) -> bool:
        return max(self.pollution_risk_score, self.budget_pressure_score, self.governance_risk_score) >= 0.3

@dataclass(frozen=True)
class GoalPriorityScore(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_goal_priority"
    explicit_user_priority: float = 0.5
    long_chain_continuity: float = 0.5
    task_urgency: float = 0.5
    dependency_unblock_value: float = 0.5
    resource_pressure: float = 0.0
    risk_pressure: float = 0.0
    becomes_execution_plan: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.becomes_execution_plan, "GoalPriorityScore.becomes_execution_plan")
        if self.becomes_execution_plan:
            raise ValueError("goal priority score cannot become execution plan")

    @property
    def priority_score(self) -> float:
        positive = weighted_mean(((self.explicit_user_priority, 1.4), (self.long_chain_continuity, 1.2), (self.task_urgency, 1.0), (self.dependency_unblock_value, 1.1)))
        pressure = weighted_mean(((self.resource_pressure, 0.6), (self.risk_pressure, 1.0)))
        return clamp01(positive * (1.0 - 0.4 * pressure))


@dataclass(frozen=True)
class CognitiveScoreConflictReport(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_score_conflict_report"
    conflicting_score_refs: tuple[str, ...] = field(default_factory=lambda: ("score:l6_phase4_conflict",))
    conflict_summary_ref: str = "summary:l6_phase4_score_conflict"
    auto_resolves_conflict: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflicting_score_refs, "CognitiveScoreConflictReport.conflicting_score_refs", required=True)
        ensure_ref_text(self.conflict_summary_ref, "CognitiveScoreConflictReport.conflict_summary_ref")
        ensure_bool(self.auto_resolves_conflict, "CognitiveScoreConflictReport.auto_resolves_conflict")
        if self.auto_resolves_conflict:
            raise ValueError("score conflict report cannot auto resolve")


@dataclass(frozen=True)
class CognitiveScorePublicProjection(Phase4ScoreBase):
    score_ref: str = "score:l6_phase4_score_public_projection"
    public_projection_ref: str = "public:l6_phase4_score_projection"
    exposes_formula_detail: bool = False
    exposes_raw_factors: bool = False
    exposes_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.public_projection_ref, "CognitiveScorePublicProjection.public_projection_ref")
        for field_name in ("exposes_formula_detail", "exposes_raw_factors", "exposes_decision"):
            ensure_bool(getattr(self, field_name), f"CognitiveScorePublicProjection.{field_name}")
        if self.exposes_formula_detail or self.exposes_raw_factors or self.exposes_decision:
            raise ValueError("score public projection must be summary-only and non-decisional")

