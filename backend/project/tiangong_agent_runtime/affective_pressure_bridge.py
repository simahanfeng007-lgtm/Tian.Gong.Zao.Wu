"""L6.41 情志压力桥。

把执行报告、质量门、预算/上下文压力等上游摘要压成七情七源与六欲六源。
本模块只做纯计算投影，不读取真实文件，不写审计，不扣预算，不执行动作。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_score

from .affective_state import SevenEmotionSignalSources, SixDesireSignalSources, clamp01


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class AffectivePressureSnapshot:
    success_signal: float = 0.0
    obstruction_signal: float = 0.0
    uncertainty_signal: float = 0.0
    reflection_load_signal: float = 0.5
    loss_signal: float = 0.0
    irreversible_threat_signal: float = 0.0
    novelty_signal: float = 0.0
    resource_pressure_signal: float = 0.0
    knowledge_gap_signal: float = 0.0
    goal_gap_signal: float = 0.5
    user_alignment_signal: float = 0.5
    entropy_signal: float = 0.5
    fatigue_signal: float = 0.0

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _score(getattr(self, field_name), f"AffectivePressureSnapshot.{field_name}")

    def to_emotion_sources(self) -> SevenEmotionSignalSources:
        return SevenEmotionSignalSources(
            joy_reward_signal=self.success_signal,
            obstruction_violation_signal=self.obstruction_signal,
            uncertainty_future_risk_signal=self.uncertainty_signal,
            reflection_load_signal=self.reflection_load_signal,
            loss_failure_signal=self.loss_signal,
            threat_irreversible_signal=self.irreversible_threat_signal,
            novelty_prediction_error_signal=self.novelty_signal,
        )

    def to_desire_sources(self) -> SixDesireSignalSources:
        return SixDesireSignalSources(
            survival_resource_boundary_signal=clamp01(0.55 * self.resource_pressure_signal + 0.45 * self.irreversible_threat_signal),
            curiosity_knowledge_gap_signal=clamp01(0.70 * self.knowledge_gap_signal + 0.30 * self.novelty_signal),
            achievement_goal_gap_signal=self.goal_gap_signal,
            connection_alignment_signal=self.user_alignment_signal,
            order_entropy_signal=clamp01(0.65 * self.entropy_signal + 0.35 * self.reflection_load_signal),
            rest_fatigue_recovery_signal=clamp01(0.70 * self.fatigue_signal + 0.30 * self.resource_pressure_signal),
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "success_signal": self.success_signal,
            "obstruction_signal": self.obstruction_signal,
            "uncertainty_signal": self.uncertainty_signal,
            "reflection_load_signal": self.reflection_load_signal,
            "loss_signal": self.loss_signal,
            "irreversible_threat_signal": self.irreversible_threat_signal,
            "novelty_signal": self.novelty_signal,
            "resource_pressure_signal": self.resource_pressure_signal,
            "knowledge_gap_signal": self.knowledge_gap_signal,
            "goal_gap_signal": self.goal_gap_signal,
            "user_alignment_signal": self.user_alignment_signal,
            "entropy_signal": self.entropy_signal,
            "fatigue_signal": self.fatigue_signal,
        }
