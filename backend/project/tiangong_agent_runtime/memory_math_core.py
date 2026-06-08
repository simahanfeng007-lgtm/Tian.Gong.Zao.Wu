"""L6.40 记忆/遗忘数学核。

本模块属于 runtime 外壳层的纯计算基础：只计算召回、晋升、遗忘与状态转移，
不写文件、不调工具、不派发模型、不修改 kernel。任何真实持久化必须经
``MemoryStoreBridge`` 或后续 L6.37 执行链治理入口。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, log, log1p
from time import time
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .biodynamic_policy_core import BioDynamicState, activation_probability, bounded_growth, dynamic_threshold, weighted_mean

L6_40_MEMORY_MATH_SCHEMA = "tiangong.l6_40.memory_math_core.v1"


def clamp01(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("score factor must be numeric, not bool")
    numeric = float(value)
    if numeric != numeric:
        raise ValueError("score factor cannot be NaN")
    return max(0.0, min(1.0, numeric))


class MemoryLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


class MemoryCategory(str, Enum):
    WORKING = "working_memory"
    EPISODIC = "episodic_memory"
    SEMANTIC = "semantic_memory"
    PROCEDURAL = "procedural_memory"
    SELF = "self_memory"
    RUNTIME = "runtime_memory"


class MemoryTransitionAction(str, Enum):
    KEEP = "keep"
    PROMOTE = "promote"
    DEMOTE = "demote"
    REVIEW = "review"
    SUPPRESS = "suppress_active_recall"


@dataclass(frozen=True)
class CategoryProfile:
    """六分类记忆权重、阈值与半衰期声明。"""

    category: MemoryCategory | str
    recall_weight: float
    promotion_threshold: float
    demotion_threshold: float
    default_half_life_seconds: float
    privacy_sensitivity: float = 0.3
    raw_content_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", MemoryCategory(self.category))
        for field_name in (
            "recall_weight",
            "promotion_threshold",
            "demotion_threshold",
            "privacy_sensitivity",
        ):
            ensure_score(getattr(self, field_name), f"CategoryProfile.{field_name}")
        if isinstance(self.default_half_life_seconds, bool) or not isinstance(self.default_half_life_seconds, (int, float)):
            raise ValueError("CategoryProfile.default_half_life_seconds must be numeric")
        if float(self.default_half_life_seconds) <= 0:
            raise ValueError("CategoryProfile.default_half_life_seconds must be positive")
        ensure_bool(self.raw_content_allowed, "CategoryProfile.raw_content_allowed")
        if self.raw_content_allowed:
            raise ValueError("L6.40 memory profiles never allow raw content exposure")

    def public_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "recall_weight": self.recall_weight,
            "promotion_threshold": self.promotion_threshold,
            "demotion_threshold": self.demotion_threshold,
            "default_half_life_seconds": self.default_half_life_seconds,
            "privacy_sensitivity": self.privacy_sensitivity,
            "raw_content_allowed": self.raw_content_allowed,
        }


DEFAULT_CATEGORY_PROFILES: dict[MemoryCategory, CategoryProfile] = {
    MemoryCategory.WORKING: CategoryProfile(MemoryCategory.WORKING, 0.80, 0.62, 0.28, 6 * 60 * 60, 0.25),
    MemoryCategory.EPISODIC: CategoryProfile(MemoryCategory.EPISODIC, 0.72, 0.66, 0.30, 30 * 24 * 60 * 60, 0.35),
    MemoryCategory.SEMANTIC: CategoryProfile(MemoryCategory.SEMANTIC, 0.92, 0.72, 0.24, 365 * 24 * 60 * 60, 0.30),
    MemoryCategory.PROCEDURAL: CategoryProfile(MemoryCategory.PROCEDURAL, 0.95, 0.70, 0.22, 720 * 24 * 60 * 60, 0.25),
    MemoryCategory.SELF: CategoryProfile(MemoryCategory.SELF, 0.62, 0.78, 0.34, 365 * 24 * 60 * 60, 0.80),
    MemoryCategory.RUNTIME: CategoryProfile(MemoryCategory.RUNTIME, 0.76, 0.68, 0.30, 24 * 60 * 60, 0.35),
}


@dataclass(frozen=True)
class DecayKernel:
    """时间衰减核：时间衰减 + 访问强化 + 成功强化。"""

    elapsed_seconds: float
    half_life_seconds: float
    reuse_count: int = 0
    success_rate: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.elapsed_seconds, bool) or not isinstance(self.elapsed_seconds, (int, float)) or self.elapsed_seconds < 0:
            raise ValueError("DecayKernel.elapsed_seconds must be non-negative number")
        if isinstance(self.half_life_seconds, bool) or not isinstance(self.half_life_seconds, (int, float)) or self.half_life_seconds <= 0:
            raise ValueError("DecayKernel.half_life_seconds must be positive number")
        if isinstance(self.reuse_count, bool) or not isinstance(self.reuse_count, int) or self.reuse_count < 0:
            raise ValueError("DecayKernel.reuse_count must be non-negative int")
        ensure_score(self.success_rate, "DecayKernel.success_rate")

    @property
    def decay(self) -> float:
        return clamp01(exp(-log(2.0) * float(self.elapsed_seconds) / float(self.half_life_seconds)))

    @property
    def reinforced_decay(self) -> float:
        return clamp01(self.decay + 0.04 * log1p(self.reuse_count) + 0.05 * self.success_rate)


@dataclass(frozen=True)
class RecallScoreVector:
    task_relevance: float = 0.5
    semantic_similarity: float = 0.5
    level_weight: float = 0.5
    freshness_decay: float = 0.5
    reuse_signal: float = 0.0
    success_signal: float = 0.0
    explicit_user_preference: float = 0.0
    procedural_fit: float = 0.0
    affective_attention_bias: float = 0.0
    privacy_risk: float = 0.0
    pollution_risk: float = 0.0
    conflict_score: float = 0.0
    uncertainty_score: float = 0.0
    tombstone_state: str = "none"
    active_recall_suppressed: bool = False
    confidence_score: float = 0.7

    def __post_init__(self) -> None:
        for field_name in (
            "task_relevance",
            "semantic_similarity",
            "level_weight",
            "freshness_decay",
            "reuse_signal",
            "success_signal",
            "explicit_user_preference",
            "procedural_fit",
            "affective_attention_bias",
            "privacy_risk",
            "pollution_risk",
            "conflict_score",
            "uncertainty_score",
            "confidence_score",
        ):
            ensure_score(getattr(self, field_name), f"RecallScoreVector.{field_name}")
        ensure_bool(self.active_recall_suppressed, "RecallScoreVector.active_recall_suppressed")
        if not isinstance(self.tombstone_state, str):
            raise ValueError("RecallScoreVector.tombstone_state must be text")

    @property
    def recall_score(self) -> float:
        if self.tombstone_state != "none" or self.active_recall_suppressed:
            return 0.0
        positive = (
            0.26 * self.task_relevance
            + 0.18 * self.semantic_similarity
            + 0.14 * self.level_weight
            + 0.12 * self.freshness_decay
            + 0.10 * self.reuse_signal
            + 0.08 * self.success_signal
            + 0.06 * self.explicit_user_preference
            + 0.04 * self.procedural_fit
            + 0.02 * self.affective_attention_bias
        )
        penalty = (
            0.20 * self.privacy_risk
            + 0.20 * self.pollution_risk
            + 0.14 * self.conflict_score
            + 0.10 * self.uncertainty_score
        )
        return clamp01(positive - penalty)

    @property
    def planner_entry_score(self) -> float:
        if self.tombstone_state != "none" or self.active_recall_suppressed:
            return 0.0
        state = BioDynamicState(
            evidence=self.confidence_score,
            drive=weighted_mean(((self.task_relevance, 0.34), (self.semantic_similarity, 0.24), (self.reuse_signal, 0.18), (self.success_signal, 0.14), (self.explicit_user_preference, 0.10))),
            uncertainty_pressure=self.uncertainty_score,
            privacy_pressure=self.privacy_risk,
            pollution_pressure=self.pollution_risk,
            conflict_pressure=self.conflict_score,
            recovery=weighted_mean(((self.level_weight, 0.45), (self.freshness_decay, 0.35), (self.procedural_fit, 0.20))),
            user_intent=self.explicit_user_preference,
        )
        return state.execution_score

    @property
    def can_enter_planner_context(self) -> bool:
        state = BioDynamicState(
            evidence=self.confidence_score,
            drive=self.recall_score,
            uncertainty_pressure=self.uncertainty_score,
            privacy_pressure=self.privacy_risk,
            pollution_pressure=self.pollution_risk,
            conflict_pressure=self.conflict_score,
            recovery=self.freshness_decay,
            user_intent=self.explicit_user_preference,
        )
        threshold = state.threshold(0.46, minimum=0.30, maximum=0.78)
        return self.tombstone_state == "none" and not self.active_recall_suppressed and self.planner_entry_score >= threshold

    @property
    def review_only(self) -> bool:
        state = BioDynamicState(
            evidence=self.confidence_score,
            drive=self.recall_score,
            uncertainty_pressure=self.uncertainty_score,
            privacy_pressure=self.privacy_risk,
            pollution_pressure=self.pollution_risk,
            conflict_pressure=self.conflict_score,
            recovery=self.freshness_decay,
        )
        review_threshold = state.threshold(0.58, minimum=0.38, maximum=0.86)
        risk_load = weighted_mean(((self.privacy_risk, 0.38), (self.pollution_risk, 0.30), (self.conflict_score, 0.20), (self.uncertainty_score, 0.12)))
        return risk_load >= review_threshold or self.planner_entry_score < state.threshold(0.36, minimum=0.20, maximum=0.62)


@dataclass(frozen=True)
class PromotionScoreVector:
    repeated_use: float = 0.0
    success_rate: float = 0.0
    evidence_strength: float = 0.0
    stability: float = 0.0
    user_confirmation: float = 0.0
    procedural_generalization: float = 0.0
    confidence_score: float = 0.7
    privacy_risk: float = 0.0
    pollution_risk: float = 0.0
    conflict_score: float = 0.0
    consecutive_above_threshold: int = 0

    def __post_init__(self) -> None:
        for field_name in (
            "repeated_use",
            "success_rate",
            "evidence_strength",
            "stability",
            "user_confirmation",
            "procedural_generalization",
            "confidence_score",
            "privacy_risk",
            "pollution_risk",
            "conflict_score",
        ):
            ensure_score(getattr(self, field_name), f"PromotionScoreVector.{field_name}")
        if isinstance(self.consecutive_above_threshold, bool) or not isinstance(self.consecutive_above_threshold, int) or self.consecutive_above_threshold < 0:
            raise ValueError("PromotionScoreVector.consecutive_above_threshold must be non-negative int")

    @property
    def promotion_score(self) -> float:
        return clamp01(
            0.24 * self.repeated_use
            + 0.20 * self.success_rate
            + 0.18 * self.evidence_strength
            + 0.14 * self.stability
            + 0.10 * self.user_confirmation
            + 0.08 * self.procedural_generalization
            + 0.06 * self.confidence_score
            - 0.25 * self.privacy_risk
            - 0.30 * self.pollution_risk
            - 0.20 * self.conflict_score
        )

    @property
    def promotion_state(self) -> BioDynamicState:
        return BioDynamicState(
            evidence=weighted_mean(((self.evidence_strength, 0.34), (self.confidence_score, 0.24), (self.stability, 0.18), (self.success_rate, 0.14), (self.user_confirmation, 0.10))),
            drive=weighted_mean(((self.repeated_use, 0.28), (self.procedural_generalization, 0.24), (self.success_rate, 0.24), (self.user_confirmation, 0.24))),
            privacy_pressure=self.privacy_risk,
            pollution_pressure=self.pollution_risk,
            conflict_pressure=self.conflict_score,
            recovery=weighted_mean(((self.stability, 0.52), (self.evidence_strength, 0.28), (self.success_rate, 0.20))),
            user_intent=self.user_confirmation,
        )

    @property
    def risk_review_score(self) -> float:
        return weighted_mean(((self.privacy_risk, 0.34), (self.pollution_risk, 0.32), (self.conflict_score, 0.22), (1.0 - self.confidence_score, 0.12)))

    @property
    def cannot_promote(self) -> bool:
        state = self.promotion_state
        adaptive_gate = state.threshold(0.62, minimum=0.42, maximum=0.90)
        return self.risk_review_score >= adaptive_gate or activation_probability(self.promotion_score, state.threshold(0.50, minimum=0.34, maximum=0.78)) < 0.42

    @property
    def hysteresis_satisfied(self) -> bool:
        required = dynamic_count_requirement(2, load=self.risk_review_score, drive=self.promotion_score, minimum=1, maximum=4)
        return self.consecutive_above_threshold >= required


@dataclass(frozen=True)
class ForgettingScoreVector:
    expiry_score: float = 0.0
    low_reuse_score: float = 0.0
    low_confidence_score: float = 0.0
    conflict_score: float = 0.0
    compression_gain: float = 0.0
    privacy_minimization_need: float = 0.0
    user_forget_signal: float = 0.0
    explicit_user_forget_request: bool = False
    protected_l5_rule_score: float = 0.0

    def __post_init__(self) -> None:
        for field_name in (
            "expiry_score",
            "low_reuse_score",
            "low_confidence_score",
            "conflict_score",
            "compression_gain",
            "privacy_minimization_need",
            "user_forget_signal",
            "protected_l5_rule_score",
        ):
            ensure_score(getattr(self, field_name), f"ForgettingScoreVector.{field_name}")
        ensure_bool(self.explicit_user_forget_request, "ForgettingScoreVector.explicit_user_forget_request")

    @property
    def forgetting_score(self) -> float:
        if self.explicit_user_forget_request:
            return 1.0
        return clamp01(
            0.28 * self.expiry_score
            + 0.20 * self.low_reuse_score
            + 0.16 * self.low_confidence_score
            + 0.12 * self.conflict_score
            + 0.10 * self.compression_gain
            + 0.08 * self.privacy_minimization_need
            + 0.06 * self.user_forget_signal
        )

    @property
    def forgetting_state(self) -> BioDynamicState:
        return BioDynamicState(
            evidence=weighted_mean(((self.expiry_score, 0.26), (self.low_confidence_score, 0.20), (self.conflict_score, 0.18), (self.privacy_minimization_need, 0.18), (self.user_forget_signal, 0.18))),
            drive=weighted_mean(((self.user_forget_signal, 0.36), (self.privacy_minimization_need, 0.26), (self.compression_gain, 0.18), (self.low_reuse_score, 0.20))),
            conflict_pressure=self.conflict_score,
            privacy_pressure=self.privacy_minimization_need,
            uncertainty_pressure=self.low_confidence_score,
            recovery=1.0 - self.protected_l5_rule_score,
            user_intent=self.user_forget_signal,
            inertia=self.protected_l5_rule_score,
        )

    @property
    def forced_review_required(self) -> bool:
        if self.explicit_user_forget_request:
            return True
        state = self.forgetting_state
        threshold = state.threshold(0.86, minimum=0.68, maximum=0.96)
        return state.execution_score >= threshold

    @property
    def l5_retention_conflict(self) -> bool:
        state = BioDynamicState(
            evidence=self.protected_l5_rule_score,
            drive=self.user_forget_signal,
            conflict_pressure=self.conflict_score,
            privacy_pressure=self.privacy_minimization_need,
            recovery=self.protected_l5_rule_score,
            user_intent=self.user_forget_signal,
        )
        return self.protected_l5_rule_score >= state.threshold(0.82, minimum=0.62, maximum=0.96) and self.forced_review_required


@dataclass(frozen=True)
class RiskCap:
    privacy_block_threshold: float = 0.80
    pollution_review_threshold: float = 0.60
    conflict_review_threshold: float = 0.70

    def __post_init__(self) -> None:
        for field_name in ("privacy_block_threshold", "pollution_review_threshold", "conflict_review_threshold"):
            ensure_score(getattr(self, field_name), f"RiskCap.{field_name}")

    def planner_context_allowed(self, vector: RecallScoreVector) -> bool:
        state = BioDynamicState(
            evidence=vector.confidence_score,
            drive=vector.recall_score,
            privacy_pressure=vector.privacy_risk,
            pollution_pressure=vector.pollution_risk,
            conflict_pressure=vector.conflict_score,
            uncertainty_pressure=vector.uncertainty_score,
            recovery=vector.freshness_decay,
        )
        privacy_limit = dynamic_threshold(self.privacy_block_threshold, load=state.load, drive=state.adaptive_drive, recovery=state.recovery, minimum=0.54, maximum=0.94)
        pollution_limit = dynamic_threshold(self.pollution_review_threshold, load=state.load, drive=state.adaptive_drive, recovery=state.recovery, minimum=0.36, maximum=0.84)
        conflict_limit = dynamic_threshold(self.conflict_review_threshold, load=state.load, drive=state.adaptive_drive, recovery=state.recovery, minimum=0.42, maximum=0.88)
        return (
            vector.privacy_risk < privacy_limit
            and vector.pollution_risk < pollution_limit
            and vector.conflict_score < conflict_limit
            and vector.can_enter_planner_context
        )


@dataclass(frozen=True)
class ConfidenceGate:
    fact_recall_threshold: float = 0.45
    promotion_threshold: float = 0.55

    def __post_init__(self) -> None:
        ensure_score(self.fact_recall_threshold, "ConfidenceGate.fact_recall_threshold")
        ensure_score(self.promotion_threshold, "ConfidenceGate.promotion_threshold")

    def can_recall_as_fact(self, confidence_score: float) -> bool:
        ensure_score(confidence_score, "ConfidenceGate.confidence_score")
        gate = dynamic_threshold(self.fact_recall_threshold, load=1.0 - confidence_score, drive=confidence_score, recovery=confidence_score, minimum=0.30, maximum=0.74)
        return float(confidence_score) >= gate

    def can_promote(self, vector: PromotionScoreVector) -> bool:
        gate = vector.promotion_state.threshold(self.promotion_threshold, minimum=0.36, maximum=0.82)
        return not vector.cannot_promote and vector.promotion_score >= gate


@dataclass(frozen=True)
class TransitionPolicy:
    """5 级记忆状态机：晋升/降级只给建议，不直接写 store。"""

    profile: CategoryProfile
    risk_cap: RiskCap = RiskCap()
    confidence_gate: ConfidenceGate = ConfidenceGate()

    def recommend(
        self,
        *,
        current_level: MemoryLevel | str,
        promotion: PromotionScoreVector,
        forgetting: ForgettingScoreVector,
    ) -> MemoryTransitionAction:
        level = MemoryLevel(current_level)
        forgetting_state = forgetting.forgetting_state
        promotion_state = promotion.promotion_state
        review_gate = forgetting_state.threshold(0.72, minimum=0.52, maximum=0.92)
        promotion_gate = promotion_state.threshold(self.profile.promotion_threshold, minimum=0.40, maximum=0.90)
        demotion_gate = forgetting_state.threshold(self.profile.demotion_threshold, minimum=0.18, maximum=0.66)
        if forgetting.forced_review_required or forgetting.forgetting_score >= review_gate:
            return MemoryTransitionAction.REVIEW
        if promotion.cannot_promote:
            return MemoryTransitionAction.REVIEW
        if promotion.promotion_score >= promotion_gate and promotion.hysteresis_satisfied:
            if level is MemoryLevel.L5:
                return MemoryTransitionAction.KEEP
            return MemoryTransitionAction.PROMOTE
        if forgetting.forgetting_score >= demotion_gate:
            if level is MemoryLevel.L1:
                return MemoryTransitionAction.SUPPRESS
            return MemoryTransitionAction.DEMOTE
        return MemoryTransitionAction.KEEP


def level_weight(level: MemoryLevel | str) -> float:
    mapping = {
        MemoryLevel.L1: 0.30,
        MemoryLevel.L2: 0.45,
        MemoryLevel.L3: 0.68,
        MemoryLevel.L4: 0.86,
        MemoryLevel.L5: 1.00,
    }
    return mapping[MemoryLevel(level)]


def success_rate(success_count: int, failure_count: int) -> float:
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in (success_count, failure_count)):
        raise ValueError("success/failure count must be non-negative int")
    total = success_count + failure_count
    if total <= 0:
        return 0.0
    return clamp01(success_count / total)


def elapsed_since(timestamp: float | None, *, now: float | None = None) -> float:
    if timestamp is None:
        return 0.0
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        raise ValueError("timestamp must be numeric")
    return max(0.0, float(now if now is not None else time()) - float(timestamp))
