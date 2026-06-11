"""L6.41 七情六欲动态情志状态模型。

本模块把情志系统建成“双层动态模型”：

1. Soul 基础底色：用户编辑 Soul 后，由公式映射为七情基础值与六欲基础值。
2. 临时波动值：由对话、任务、失败、压力、成功、异常等信号动态计算。
3. 当前总值：current_total = clamp01(soul_baseline + temporary_delta)。

边界：
- 七情影响语言状态逻辑：表达温度、结构密度、复核密度、风险说明、异常检查。
- 六欲影响做事方式：闭环推进、探索、协作、秩序、边界稳定、长链节奏。
- 情志状态只产出 Planner 可消费 hint；不授权、不拒绝、不调工具、不调模型、不扣预算、不写记忆。

建模参考：情感神经科学的基本情绪系统、认知评价/强化学习模型、稳态/异稳态调节。
代码中不把这些理论变成医学判断，只借用“基础倾向 + 动态刺激 + 衰减回稳 + 压力耦合”的工程结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, log
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, stable_digest
from tiangong_kernel.l6_plugins.cognitive_continuity.affective.vectors import (
    SevenEmotionSignalVector,
    SixDesireTendencyVector,
)

L6_41_AFFECTIVE_STATE_SCHEMA = "tiangong.l6_41.affective_state.v2"


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


def _soul_ref(value: str, field_name: str) -> None:
    """Validate an internal Soul reference.

    Soul refs often include tokens such as ``soul_profile:variant``; the
    generic ref validator treats the substring ``file:`` inside ``profile:``
    as a live-address marker. This local validator keeps the same compact-text
    and live-endpoint protections while allowing internal profile refs.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    if len(value) > 256 or any(marker in value for marker in ("\n", "\r", "\x00")):
        raise ValueError(f"{field_name} must be compact ref text")
    lowered = value.lower()
    forbidden_live_prefixes = ("http:", "https:", "file:", "ws:", "wss:", "postgres:", "mysql:", "mongodb:", "redis:")
    if "://" in lowered or lowered.startswith(forbidden_live_prefixes):
        raise ValueError(f"{field_name} cannot contain live address marker")
    if not lowered.startswith(("affective:", "soul:", "ref:", "state:", "digest:", "test:")):
        raise ValueError(f"{field_name} must be an internal Soul/affective ref")


def _number(value: float, field_name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric, not bool")
    numeric = float(value)
    if numeric != numeric or numeric < minimum:
        raise ValueError(f"{field_name} must be non-negative finite number")
    return numeric


def _delta(value: float, field_name: str, *, minimum: float = -1.0, maximum: float = 1.0) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric delta, not bool")
    numeric = float(value)
    if numeric != numeric or numeric < minimum or numeric > maximum:
        raise ValueError(f"{field_name} must be within {minimum}..{maximum}")


def clamp01(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("score factor must be numeric, not bool")
    numeric = float(value)
    if numeric != numeric:
        raise ValueError("score factor cannot be NaN")
    return max(0.0, min(1.0, numeric))


def clamp_delta(value: float, *, limit: float = 1.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("delta factor must be numeric, not bool")
    numeric = float(value)
    if numeric != numeric:
        raise ValueError("delta factor cannot be NaN")
    limit_value = _number(limit, "limit", minimum=0.0)
    return max(-limit_value, min(limit_value, numeric))


def _ema(previous: float, target: float, alpha: float) -> float:
    return clamp01((1.0 - alpha) * previous + alpha * target)


def _ema_delta(previous: float, target: float, alpha: float, *, limit: float) -> float:
    return clamp_delta((1.0 - alpha) * previous + alpha * target, limit=limit)


def _decay_retention(elapsed_seconds: float, half_life_seconds: float) -> float:
    elapsed = _number(elapsed_seconds, "elapsed_seconds")
    half_life = _number(half_life_seconds, "half_life_seconds", minimum=1e-9)
    return clamp01(exp(-log(2.0) * elapsed / half_life))


@dataclass(frozen=True)
class SevenEmotionSignalSources:
    """七情七源。每一情有一个主信号源，符合“七情分源”口径。

    - 喜 joy_reward_signal：成功、收益、完成感。
    - 怒 obstruction_violation_signal：阻滞、重复失败、边界被破坏。
    - 忧 uncertainty_future_risk_signal：不确定、待办悬而未决、未来风险。
    - 思 reflection_load_signal：复杂推理、复核负载、结构化需求。
    - 悲 loss_failure_signal：失败、损失、不可恢复结果。
    - 恐 threat_irreversible_signal：A5、凭证、隐私、不可逆副作用。
    - 惊 novelty_prediction_error_signal：新奇、异常、预测误差。
    """

    joy_reward_signal: float = 0.0
    obstruction_violation_signal: float = 0.0
    uncertainty_future_risk_signal: float = 0.0
    reflection_load_signal: float = 0.5
    loss_failure_signal: float = 0.0
    threat_irreversible_signal: float = 0.0
    novelty_prediction_error_signal: float = 0.0

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _score(getattr(self, field_name), f"SevenEmotionSignalSources.{field_name}")

    def public_dict(self) -> dict[str, float]:
        return {
            "joy_reward_signal": self.joy_reward_signal,
            "obstruction_violation_signal": self.obstruction_violation_signal,
            "uncertainty_future_risk_signal": self.uncertainty_future_risk_signal,
            "reflection_load_signal": self.reflection_load_signal,
            "loss_failure_signal": self.loss_failure_signal,
            "threat_irreversible_signal": self.threat_irreversible_signal,
            "novelty_prediction_error_signal": self.novelty_prediction_error_signal,
        }


@dataclass(frozen=True)
class SixDesireSignalSources:
    """六欲六源。六欲只影响做事方式，不成为真实 action。"""

    survival_resource_boundary_signal: float = 0.5
    curiosity_knowledge_gap_signal: float = 0.5
    achievement_goal_gap_signal: float = 0.5
    connection_alignment_signal: float = 0.5
    order_entropy_signal: float = 0.5
    rest_fatigue_recovery_signal: float = 0.0

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _score(getattr(self, field_name), f"SixDesireSignalSources.{field_name}")

    def public_dict(self) -> dict[str, float]:
        return {
            "survival_resource_boundary_signal": self.survival_resource_boundary_signal,
            "curiosity_knowledge_gap_signal": self.curiosity_knowledge_gap_signal,
            "achievement_goal_gap_signal": self.achievement_goal_gap_signal,
            "connection_alignment_signal": self.connection_alignment_signal,
            "order_entropy_signal": self.order_entropy_signal,
            "rest_fatigue_recovery_signal": self.rest_fatigue_recovery_signal,
        }


@dataclass(frozen=True)
class SoulAffectiveProfile:
    """Soul 到情志基础值的输入侧摘要。

    真实 Soul 正文不进入 public projection；这里只接收 Soul 解析后的归一化结构分量。
    每个字段均为 0..1 的稳定人格/底色倾向。
    """

    soul_ref: str = "affective:soul_profile"
    warmth: float = 0.50
    boundary_sensitivity: float = 0.50
    reflection_depth: float = 0.50
    resilience: float = 0.55
    novelty_openness: float = 0.50
    achievement_drive: float = 0.55
    connection_drive: float = 0.50
    order_drive: float = 0.52
    recovery_preference: float = 0.18

    def __post_init__(self) -> None:
        _soul_ref(self.soul_ref, "SoulAffectiveProfile.soul_ref")
        for field_name in (
            "warmth",
            "boundary_sensitivity",
            "reflection_depth",
            "resilience",
            "novelty_openness",
            "achievement_drive",
            "connection_drive",
            "order_drive",
            "recovery_preference",
        ):
            _score(getattr(self, field_name), f"SoulAffectiveProfile.{field_name}")

    @property
    def digest(self) -> str:
        return stable_digest(self.public_dict())

    def public_dict(self) -> dict[str, Any]:
        return {
            "soul_ref": self.soul_ref,
            "warmth": self.warmth,
            "boundary_sensitivity": self.boundary_sensitivity,
            "reflection_depth": self.reflection_depth,
            "resilience": self.resilience,
            "novelty_openness": self.novelty_openness,
            "achievement_drive": self.achievement_drive,
            "connection_drive": self.connection_drive,
            "order_drive": self.order_drive,
            "recovery_preference": self.recovery_preference,
        }


@dataclass(frozen=True)
class AffectiveBaseline:
    """Soul 生成的七情/六欲基础底色。"""

    soul_digest: str
    emotion_baseline: SevenEmotionSignalVector
    desire_baseline: SixDesireTendencyVector
    from_soul: bool = True
    stable_baseline: bool = True
    raw_soul_visible: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.soul_digest, str) or not self.soul_digest:
            raise ValueError("AffectiveBaseline.soul_digest must be text")
        for field_name in ("from_soul", "stable_baseline", "raw_soul_visible"):
            ensure_bool(getattr(self, field_name), f"AffectiveBaseline.{field_name}")
        if not self.from_soul or not self.stable_baseline or self.raw_soul_visible:
            raise ValueError("affective baseline must be stable Soul-derived summary without raw Soul disclosure")

    @classmethod
    def from_soul_profile(cls, profile: SoulAffectiveProfile | None = None) -> "AffectiveBaseline":
        p = profile or SoulAffectiveProfile()
        emotion = SevenEmotionSignalVector(
            joy=clamp01(0.16 + 0.42 * p.warmth + 0.20 * p.resilience + 0.08 * p.connection_drive),
            anger=clamp01(0.03 + 0.26 * p.boundary_sensitivity + 0.11 * (1.0 - p.warmth)),
            worry=clamp01(0.06 + 0.30 * p.boundary_sensitivity + 0.20 * (1.0 - p.resilience)),
            thoughtfulness=clamp01(0.20 + 0.48 * p.reflection_depth + 0.16 * p.order_drive),
            sadness=clamp01(0.03 + 0.24 * (1.0 - p.resilience) + 0.10 * p.recovery_preference),
            fear=clamp01(0.03 + 0.34 * p.boundary_sensitivity + 0.12 * (1.0 - p.resilience)),
            surprise=clamp01(0.04 + 0.42 * p.novelty_openness),
        )
        desire = SixDesireTendencyVector(
            survival=clamp01(0.18 + 0.48 * p.boundary_sensitivity + 0.18 * (1.0 - p.resilience)),
            curiosity=clamp01(0.18 + 0.60 * p.novelty_openness + 0.08 * p.reflection_depth),
            achievement=clamp01(0.20 + 0.58 * p.achievement_drive + 0.08 * p.resilience),
            connection=clamp01(0.20 + 0.54 * p.connection_drive + 0.12 * p.warmth),
            order=clamp01(0.20 + 0.54 * p.order_drive + 0.12 * p.reflection_depth),
            rest=clamp01(0.04 + 0.56 * p.recovery_preference + 0.12 * (1.0 - p.resilience)),
        )
        return cls(soul_digest=p.digest, emotion_baseline=emotion, desire_baseline=desire)

    @property
    def digest(self) -> str:
        return stable_digest(self.public_dict())

    def public_dict(self) -> dict[str, Any]:
        return {
            "soul_digest": self.soul_digest,
            "emotion_baseline": {
                "joy": self.emotion_baseline.joy,
                "anger": self.emotion_baseline.anger,
                "worry": self.emotion_baseline.worry,
                "thoughtfulness": self.emotion_baseline.thoughtfulness,
                "sadness": self.emotion_baseline.sadness,
                "fear": self.emotion_baseline.fear,
                "surprise": self.emotion_baseline.surprise,
            },
            "desire_baseline": {
                "survival": self.desire_baseline.survival,
                "curiosity": self.desire_baseline.curiosity,
                "achievement": self.desire_baseline.achievement,
                "connection": self.desire_baseline.connection,
                "order": self.desire_baseline.order,
                "rest": self.desire_baseline.rest,
            },
            "from_soul": self.from_soul,
            "stable_baseline": self.stable_baseline,
            "raw_soul_visible": self.raw_soul_visible,
        }


@dataclass(frozen=True)
class SevenEmotionTemporaryDelta:
    """七情临时波动值。范围 -1..1，可正可负。"""

    joy: float = 0.0
    anger: float = 0.0
    worry: float = 0.0
    thoughtfulness: float = 0.0
    sadness: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _delta(getattr(self, field_name), f"SevenEmotionTemporaryDelta.{field_name}")

    def public_dict(self) -> dict[str, float]:
        return {
            "joy": self.joy,
            "anger": self.anger,
            "worry": self.worry,
            "thoughtfulness": self.thoughtfulness,
            "sadness": self.sadness,
            "fear": self.fear,
            "surprise": self.surprise,
        }


@dataclass(frozen=True)
class SixDesireTemporaryDelta:
    """六欲临时波动值。范围 -1..1，可正可负。"""

    survival: float = 0.0
    curiosity: float = 0.0
    achievement: float = 0.0
    connection: float = 0.0
    order: float = 0.0
    rest: float = 0.0

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _delta(getattr(self, field_name), f"SixDesireTemporaryDelta.{field_name}")

    def public_dict(self) -> dict[str, float]:
        return {
            "survival": self.survival,
            "curiosity": self.curiosity,
            "achievement": self.achievement,
            "connection": self.connection,
            "order": self.order,
            "rest": self.rest,
        }


@dataclass(frozen=True)
class AffectiveDynamicsConfig:
    """情志动态核参数。所有参数均为纯数学参数。"""

    emotion_alpha: float = 0.38
    desire_alpha: float = 0.32
    emotion_half_life_seconds: float = 1800.0
    desire_half_life_seconds: float = 3600.0
    temporary_delta_limit: float = 0.72
    stress_coupling_strength: float = 0.12
    language_logic_sensitivity: float = 0.70
    doing_mode_sensitivity: float = 0.70
    reset_temporary_when_soul_changes: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "emotion_alpha",
            "desire_alpha",
            "temporary_delta_limit",
            "stress_coupling_strength",
            "language_logic_sensitivity",
            "doing_mode_sensitivity",
        ):
            _score(getattr(self, field_name), f"AffectiveDynamicsConfig.{field_name}")
        _number(self.emotion_half_life_seconds, "AffectiveDynamicsConfig.emotion_half_life_seconds", minimum=1e-9)
        _number(self.desire_half_life_seconds, "AffectiveDynamicsConfig.desire_half_life_seconds", minimum=1e-9)
        ensure_bool(self.reset_temporary_when_soul_changes, "AffectiveDynamicsConfig.reset_temporary_when_soul_changes")


@dataclass(frozen=True)
class LanguageStateLogic:
    """七情对语言状态逻辑的降维结果。"""

    warmth: float
    structure_density: float
    risk_explanation_density: float
    anomaly_check_density: float
    brevity_pressure: float
    verification_density: float
    no_sycophancy_guard: bool = True
    no_permission_effect: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "warmth",
            "structure_density",
            "risk_explanation_density",
            "anomaly_check_density",
            "brevity_pressure",
            "verification_density",
        ):
            _score(getattr(self, field_name), f"LanguageStateLogic.{field_name}")
        ensure_bool(self.no_sycophancy_guard, "LanguageStateLogic.no_sycophancy_guard")
        ensure_bool(self.no_permission_effect, "LanguageStateLogic.no_permission_effect")
        if not self.no_sycophancy_guard or not self.no_permission_effect:
            raise ValueError("language state logic cannot weaken safety or become permission")

    def public_dict(self) -> dict[str, Any]:
        return {
            "warmth": self.warmth,
            "structure_density": self.structure_density,
            "risk_explanation_density": self.risk_explanation_density,
            "anomaly_check_density": self.anomaly_check_density,
            "brevity_pressure": self.brevity_pressure,
            "verification_density": self.verification_density,
            "no_sycophancy_guard": self.no_sycophancy_guard,
            "no_permission_effect": self.no_permission_effect,
        }


@dataclass(frozen=True)
class DoingModeLogic:
    """六欲对做事方式的降维结果。"""

    task_closure_bias: float
    exploration_bias: float
    collaboration_bias: float
    structure_bias: float
    boundary_stability_bias: float
    pacing_compression_bias: float
    same_risk_ranking_only: bool = True
    no_action_dispatch: bool = True
    no_budget_mutation: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "task_closure_bias",
            "exploration_bias",
            "collaboration_bias",
            "structure_bias",
            "boundary_stability_bias",
            "pacing_compression_bias",
        ):
            _score(getattr(self, field_name), f"DoingModeLogic.{field_name}")
        for field_name in ("same_risk_ranking_only", "no_action_dispatch", "no_budget_mutation"):
            ensure_bool(getattr(self, field_name), f"DoingModeLogic.{field_name}")
        if not self.same_risk_ranking_only or not self.no_action_dispatch or not self.no_budget_mutation:
            raise ValueError("doing mode logic can only rank same-risk planner candidates")

    def public_dict(self) -> dict[str, Any]:
        return {
            "task_closure_bias": self.task_closure_bias,
            "exploration_bias": self.exploration_bias,
            "collaboration_bias": self.collaboration_bias,
            "structure_bias": self.structure_bias,
            "boundary_stability_bias": self.boundary_stability_bias,
            "pacing_compression_bias": self.pacing_compression_bias,
            "same_risk_ranking_only": self.same_risk_ranking_only,
            "no_action_dispatch": self.no_action_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
        }


@dataclass(frozen=True)
class AffectiveState:
    """L6.41 动态情志状态。"""

    affective_baseline: AffectiveBaseline = field(default_factory=AffectiveBaseline.from_soul_profile)
    emotion_temporary_delta: SevenEmotionTemporaryDelta = field(default_factory=SevenEmotionTemporaryDelta)
    desire_temporary_delta: SixDesireTemporaryDelta = field(default_factory=SixDesireTemporaryDelta)
    emotion_vector: SevenEmotionSignalVector = field(default_factory=lambda: AffectiveBaseline.from_soul_profile().emotion_baseline)
    desire_vector: SixDesireTendencyVector = field(default_factory=lambda: AffectiveBaseline.from_soul_profile().desire_baseline)
    language_logic: LanguageStateLogic = field(
        default_factory=lambda: LanguageStateLogic(
            warmth=0.5,
            structure_density=0.5,
            risk_explanation_density=0.2,
            anomaly_check_density=0.1,
            brevity_pressure=0.2,
            verification_density=0.4,
        )
    )
    doing_logic: DoingModeLogic = field(
        default_factory=lambda: DoingModeLogic(
            task_closure_bias=0.5,
            exploration_bias=0.5,
            collaboration_bias=0.5,
            structure_bias=0.5,
            boundary_stability_bias=0.5,
            pacing_compression_bias=0.2,
        )
    )
    allostatic_load: float = 0.0
    affective_momentum: float = 0.0
    composition_rule: str = "current_total = clamp01(soul_baseline + temporary_delta)"
    dynamic_state: bool = True
    planner_hint_only: bool = True
    no_authorization: bool = True
    no_refusal_authority: bool = True
    no_tool_dispatch: bool = True
    no_model_dispatch: bool = True
    no_budget_mutation: bool = True
    schema_version: str = L6_41_AFFECTIVE_STATE_SCHEMA

    def __post_init__(self) -> None:
        for field_name in ("allostatic_load", "affective_momentum"):
            _score(getattr(self, field_name), f"AffectiveState.{field_name}")
        for field_name in (
            "dynamic_state",
            "planner_hint_only",
            "no_authorization",
            "no_refusal_authority",
            "no_tool_dispatch",
            "no_model_dispatch",
            "no_budget_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"AffectiveState.{field_name}")
        if not (
            self.dynamic_state
            and self.planner_hint_only
            and self.no_authorization
            and self.no_refusal_authority
            and self.no_tool_dispatch
            and self.no_model_dispatch
            and self.no_budget_mutation
        ):
            raise ValueError("affective state is dynamic hint only and cannot execute or authorize")
        self._validate_composition()

    def _validate_composition(self) -> None:
        pairs = (
            ("joy", self.emotion_vector.joy, self.affective_baseline.emotion_baseline.joy, self.emotion_temporary_delta.joy),
            ("anger", self.emotion_vector.anger, self.affective_baseline.emotion_baseline.anger, self.emotion_temporary_delta.anger),
            ("worry", self.emotion_vector.worry, self.affective_baseline.emotion_baseline.worry, self.emotion_temporary_delta.worry),
            ("thoughtfulness", self.emotion_vector.thoughtfulness, self.affective_baseline.emotion_baseline.thoughtfulness, self.emotion_temporary_delta.thoughtfulness),
            ("sadness", self.emotion_vector.sadness, self.affective_baseline.emotion_baseline.sadness, self.emotion_temporary_delta.sadness),
            ("fear", self.emotion_vector.fear, self.affective_baseline.emotion_baseline.fear, self.emotion_temporary_delta.fear),
            ("surprise", self.emotion_vector.surprise, self.affective_baseline.emotion_baseline.surprise, self.emotion_temporary_delta.surprise),
            ("survival", self.desire_vector.survival, self.affective_baseline.desire_baseline.survival, self.desire_temporary_delta.survival),
            ("curiosity", self.desire_vector.curiosity, self.affective_baseline.desire_baseline.curiosity, self.desire_temporary_delta.curiosity),
            ("achievement", self.desire_vector.achievement, self.affective_baseline.desire_baseline.achievement, self.desire_temporary_delta.achievement),
            ("connection", self.desire_vector.connection, self.affective_baseline.desire_baseline.connection, self.desire_temporary_delta.connection),
            ("order", self.desire_vector.order, self.affective_baseline.desire_baseline.order, self.desire_temporary_delta.order),
            ("rest", self.desire_vector.rest, self.affective_baseline.desire_baseline.rest, self.desire_temporary_delta.rest),
        )
        for name, total, baseline, delta in pairs:
            expected = clamp01(baseline + delta)
            if abs(total - expected) > 1e-9:
                raise ValueError(f"{name} violates affective composition rule")

    @property
    def dominant_emotion(self) -> str:
        values = {
            "joy": self.emotion_vector.joy,
            "anger": self.emotion_vector.anger,
            "worry": self.emotion_vector.worry,
            "thoughtfulness": self.emotion_vector.thoughtfulness,
            "sadness": self.emotion_vector.sadness,
            "fear": self.emotion_vector.fear,
            "surprise": self.emotion_vector.surprise,
        }
        return max(values, key=values.get)

    @property
    def dominant_desire(self) -> str:
        values = {
            "survival": self.desire_vector.survival,
            "curiosity": self.desire_vector.curiosity,
            "achievement": self.desire_vector.achievement,
            "connection": self.desire_vector.connection,
            "order": self.desire_vector.order,
            "rest": self.desire_vector.rest,
        }
        return max(values, key=values.get)

    @property
    def digest(self) -> str:
        return stable_digest(self.public_dict())

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "composition_rule": self.composition_rule,
            "affective_baseline": self.affective_baseline.public_dict(),
            "emotion_temporary_delta": self.emotion_temporary_delta.public_dict(),
            "desire_temporary_delta": self.desire_temporary_delta.public_dict(),
            "emotion_vector": {
                "joy": self.emotion_vector.joy,
                "anger": self.emotion_vector.anger,
                "worry": self.emotion_vector.worry,
                "thoughtfulness": self.emotion_vector.thoughtfulness,
                "sadness": self.emotion_vector.sadness,
                "fear": self.emotion_vector.fear,
                "surprise": self.emotion_vector.surprise,
                "expression_only": self.emotion_vector.expression_only,
                "permission_bypass": self.emotion_vector.permission_bypass,
                "tool_dispatch": self.emotion_vector.tool_dispatch,
                "dispatches_model": self.emotion_vector.dispatches_model,
            },
            "desire_vector": {
                "survival": self.desire_vector.survival,
                "curiosity": self.desire_vector.curiosity,
                "achievement": self.desire_vector.achievement,
                "connection": self.desire_vector.connection,
                "order": self.desire_vector.order,
                "rest": self.desire_vector.rest,
                "candidate_ranking_only": self.desire_vector.candidate_ranking_only,
                "action_dispatch": self.desire_vector.action_dispatch,
                "permission_bypass": self.desire_vector.permission_bypass,
            },
            "language_logic": self.language_logic.public_dict(),
            "doing_logic": self.doing_logic.public_dict(),
            "allostatic_load": self.allostatic_load,
            "affective_momentum": self.affective_momentum,
            "dominant_emotion": self.dominant_emotion,
            "dominant_desire": self.dominant_desire,
            "planner_hint_only": self.planner_hint_only,
            "no_authorization": self.no_authorization,
            "no_refusal_authority": self.no_refusal_authority,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_model_dispatch": self.no_model_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
        }


class AffectiveStateEngine:
    """Soul 基础值 + 临时波动值的动态计算器。"""

    def __init__(self, config: AffectiveDynamicsConfig | None = None) -> None:
        self.config = config or AffectiveDynamicsConfig()

    def evolve(
        self,
        emotion_sources: SevenEmotionSignalSources,
        desire_sources: SixDesireSignalSources,
        *,
        soul_baseline: AffectiveBaseline | None = None,
        previous_state: AffectiveState | None = None,
        elapsed_seconds: float = 0.0,
    ) -> AffectiveState:
        baseline = soul_baseline or (previous_state.affective_baseline if previous_state else AffectiveBaseline.from_soul_profile())
        emotion_retention = _decay_retention(elapsed_seconds, self.config.emotion_half_life_seconds)
        desire_retention = _decay_retention(elapsed_seconds, self.config.desire_half_life_seconds)
        soul_changed = bool(previous_state and previous_state.affective_baseline.digest != baseline.digest)

        prev_emotion_delta = (
            SevenEmotionTemporaryDelta()
            if soul_changed and self.config.reset_temporary_when_soul_changes
            else (previous_state.emotion_temporary_delta if previous_state else SevenEmotionTemporaryDelta())
        )
        prev_desire_delta = (
            SixDesireTemporaryDelta()
            if soul_changed and self.config.reset_temporary_when_soul_changes
            else (previous_state.desire_temporary_delta if previous_state else SixDesireTemporaryDelta())
        )

        stress = clamp01(
            0.22 * emotion_sources.obstruction_violation_signal
            + 0.20 * emotion_sources.uncertainty_future_risk_signal
            + 0.20 * emotion_sources.loss_failure_signal
            + 0.24 * emotion_sources.threat_irreversible_signal
            + 0.14 * desire_sources.rest_fatigue_recovery_signal
        )
        positive = clamp01(0.60 * emotion_sources.joy_reward_signal + 0.40 * desire_sources.achievement_goal_gap_signal)

        emotion_targets = {
            "joy": clamp01(0.12 + 0.78 * emotion_sources.joy_reward_signal - 0.20 * stress),
            "anger": clamp01(0.08 + 0.74 * emotion_sources.obstruction_violation_signal + 0.12 * stress),
            "worry": clamp01(0.10 + 0.66 * emotion_sources.uncertainty_future_risk_signal + 0.18 * stress),
            "thoughtfulness": clamp01(0.22 + 0.58 * emotion_sources.reflection_load_signal + 0.12 * desire_sources.order_entropy_signal),
            "sadness": clamp01(0.06 + 0.76 * emotion_sources.loss_failure_signal + 0.08 * stress - 0.10 * positive),
            "fear": clamp01(0.06 + 0.80 * emotion_sources.threat_irreversible_signal + 0.12 * stress),
            "surprise": clamp01(0.08 + 0.82 * emotion_sources.novelty_prediction_error_signal + 0.06 * stress),
        }

        baseline_emotion = baseline.emotion_baseline
        emotion_delta = self._emotion_delta(
            baseline_emotion=baseline_emotion,
            targets=emotion_targets,
            previous_delta=prev_emotion_delta,
            retention=emotion_retention,
        )
        emotion_vector = SevenEmotionSignalVector(
            joy=clamp01(baseline_emotion.joy + emotion_delta.joy),
            anger=clamp01(baseline_emotion.anger + emotion_delta.anger),
            worry=clamp01(baseline_emotion.worry + emotion_delta.worry),
            thoughtfulness=clamp01(baseline_emotion.thoughtfulness + emotion_delta.thoughtfulness),
            sadness=clamp01(baseline_emotion.sadness + emotion_delta.sadness),
            fear=clamp01(baseline_emotion.fear + emotion_delta.fear),
            surprise=clamp01(baseline_emotion.surprise + emotion_delta.surprise),
        )

        desire_targets = {
            "survival": clamp01(0.20 + 0.72 * desire_sources.survival_resource_boundary_signal + 0.10 * emotion_vector.fear),
            "curiosity": clamp01(0.18 + 0.70 * desire_sources.curiosity_knowledge_gap_signal + 0.10 * emotion_vector.surprise - 0.12 * emotion_vector.fear),
            "achievement": clamp01(0.18 + 0.72 * desire_sources.achievement_goal_gap_signal + 0.08 * emotion_vector.joy - 0.10 * desire_sources.rest_fatigue_recovery_signal),
            "connection": clamp01(0.16 + 0.72 * desire_sources.connection_alignment_signal + 0.08 * emotion_vector.joy - 0.08 * emotion_vector.anger),
            "order": clamp01(0.18 + 0.70 * desire_sources.order_entropy_signal + 0.10 * emotion_vector.thoughtfulness + 0.08 * emotion_vector.worry),
            "rest": clamp01(0.08 + 0.76 * desire_sources.rest_fatigue_recovery_signal + 0.14 * stress),
        }
        baseline_desire = baseline.desire_baseline
        desire_delta = self._desire_delta(
            baseline_desire=baseline_desire,
            targets=desire_targets,
            previous_delta=prev_desire_delta,
            retention=desire_retention,
        )
        desire_vector = SixDesireTendencyVector(
            survival=clamp01(baseline_desire.survival + desire_delta.survival),
            curiosity=clamp01(baseline_desire.curiosity + desire_delta.curiosity),
            achievement=clamp01(baseline_desire.achievement + desire_delta.achievement),
            connection=clamp01(baseline_desire.connection + desire_delta.connection),
            order=clamp01(baseline_desire.order + desire_delta.order),
            rest=clamp01(baseline_desire.rest + desire_delta.rest),
        )

        language_logic = self._language_logic(emotion_vector, desire_vector)
        doing_logic = self._doing_logic(emotion_vector, desire_vector)
        previous_load = previous_state.allostatic_load if previous_state and not soul_changed else 0.0
        allostatic_load = _ema(previous_load, stress, self.config.stress_coupling_strength)
        previous_intensity = previous_state.emotion_vector.intensity_score if previous_state and not soul_changed else baseline_emotion.intensity_score
        affective_momentum = clamp01(abs(emotion_vector.intensity_score - previous_intensity))
        return AffectiveState(
            affective_baseline=baseline,
            emotion_temporary_delta=emotion_delta,
            desire_temporary_delta=desire_delta,
            emotion_vector=emotion_vector,
            desire_vector=desire_vector,
            language_logic=language_logic,
            doing_logic=doing_logic,
            allostatic_load=allostatic_load,
            affective_momentum=affective_momentum,
        )

    def _emotion_delta(
        self,
        *,
        baseline_emotion: SevenEmotionSignalVector,
        targets: dict[str, float],
        previous_delta: SevenEmotionTemporaryDelta,
        retention: float,
    ) -> SevenEmotionTemporaryDelta:
        limit = self.config.temporary_delta_limit

        def next_delta(name: str, baseline_value: float, prev_value: float) -> float:
            decayed_previous = clamp_delta(retention * prev_value, limit=limit)
            target_delta = clamp_delta(targets[name] - baseline_value, limit=limit)
            return _ema_delta(decayed_previous, target_delta, self.config.emotion_alpha, limit=limit)

        return SevenEmotionTemporaryDelta(
            joy=next_delta("joy", baseline_emotion.joy, previous_delta.joy),
            anger=next_delta("anger", baseline_emotion.anger, previous_delta.anger),
            worry=next_delta("worry", baseline_emotion.worry, previous_delta.worry),
            thoughtfulness=next_delta("thoughtfulness", baseline_emotion.thoughtfulness, previous_delta.thoughtfulness),
            sadness=next_delta("sadness", baseline_emotion.sadness, previous_delta.sadness),
            fear=next_delta("fear", baseline_emotion.fear, previous_delta.fear),
            surprise=next_delta("surprise", baseline_emotion.surprise, previous_delta.surprise),
        )

    def _desire_delta(
        self,
        *,
        baseline_desire: SixDesireTendencyVector,
        targets: dict[str, float],
        previous_delta: SixDesireTemporaryDelta,
        retention: float,
    ) -> SixDesireTemporaryDelta:
        limit = self.config.temporary_delta_limit

        def next_delta(name: str, baseline_value: float, prev_value: float, alpha: float | None = None) -> float:
            decayed_previous = clamp_delta(retention * prev_value, limit=limit)
            target_delta = clamp_delta(targets[name] - baseline_value, limit=limit)
            return _ema_delta(decayed_previous, target_delta, alpha or self.config.desire_alpha, limit=limit)

        rest_alpha = clamp01(self.config.desire_alpha + 0.50 * max(0.0, targets["rest"] - baseline_desire.rest))
        return SixDesireTemporaryDelta(
            survival=next_delta("survival", baseline_desire.survival, previous_delta.survival),
            curiosity=next_delta("curiosity", baseline_desire.curiosity, previous_delta.curiosity),
            achievement=next_delta("achievement", baseline_desire.achievement, previous_delta.achievement),
            connection=next_delta("connection", baseline_desire.connection, previous_delta.connection),
            order=next_delta("order", baseline_desire.order, previous_delta.order),
            rest=next_delta("rest", baseline_desire.rest, previous_delta.rest, rest_alpha),
        )

    def _language_logic(
        self,
        emotion: SevenEmotionSignalVector,
        desire: SixDesireTendencyVector,
    ) -> LanguageStateLogic:
        return LanguageStateLogic(
            warmth=clamp01(0.40 + 0.34 * emotion.joy + 0.18 * desire.connection - 0.18 * emotion.anger - 0.12 * emotion.fear),
            structure_density=clamp01(0.30 + 0.42 * emotion.thoughtfulness + 0.24 * desire.order + 0.10 * emotion.worry),
            risk_explanation_density=clamp01(0.22 + 0.40 * emotion.fear + 0.32 * emotion.worry + 0.12 * desire.survival),
            anomaly_check_density=clamp01(0.12 + 0.58 * emotion.surprise + 0.12 * emotion.fear + 0.08 * emotion.anger),
            brevity_pressure=clamp01(0.12 + 0.46 * desire.rest + 0.16 * emotion.sadness + 0.08 * emotion.fear),
            verification_density=clamp01(0.24 + 0.28 * emotion.thoughtfulness + 0.22 * emotion.worry + 0.18 * emotion.fear + 0.10 * desire.order),
        )

    def _doing_logic(
        self,
        emotion: SevenEmotionSignalVector,
        desire: SixDesireTendencyVector,
    ) -> DoingModeLogic:
        return DoingModeLogic(
            task_closure_bias=clamp01(0.28 + 0.46 * desire.achievement + 0.18 * desire.order - 0.16 * desire.rest),
            exploration_bias=clamp01(0.18 + 0.58 * desire.curiosity + 0.16 * emotion.surprise - 0.18 * emotion.fear),
            collaboration_bias=clamp01(0.20 + 0.56 * desire.connection + 0.12 * emotion.joy - 0.12 * emotion.anger),
            structure_bias=clamp01(0.24 + 0.50 * desire.order + 0.16 * emotion.thoughtfulness),
            boundary_stability_bias=clamp01(0.24 + 0.44 * desire.survival + 0.18 * emotion.fear + 0.10 * emotion.worry),
            pacing_compression_bias=clamp01(0.12 + 0.58 * desire.rest + 0.12 * emotion.sadness + 0.08 * emotion.fear),
        )
