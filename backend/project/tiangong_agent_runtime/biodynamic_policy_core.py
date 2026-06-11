"""L6.72 生物动态策略数学底座。

本模块只提供纯函数/纯数据公式，不写文件、不调工具、不创建线程、不修改 Runtime
状态。设计目标是把原先散落在记忆、遗忘、执行力和生命周期中的固定阈值，统一
转成“驱动力-压力-证据-恢复力”的连续动态模型。

模型隐喻：
- drive：趋近/行动驱动力，类似动机、成就、好奇、任务价值；
- load：压力/疲劳/冲突负荷，类似 allostatic load；
- evidence：证据积累强度，类似 drift-diffusion 的 evidence accumulation；
- recovery：可逆性/回滚/资源恢复力，避免治理把执行力压死。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log1p

L6_72_BIODYNAMIC_POLICY_SCHEMA = "tiangong.l6_72.biodynamic_policy_core.v1"


def clamp01(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("biodynamic score must be numeric, not bool")
    numeric = float(value)
    if numeric != numeric:
        raise ValueError("biodynamic score cannot be NaN")
    return max(0.0, min(1.0, numeric))


def sigmoid(value: float, *, slope: float = 8.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("sigmoid input must be numeric")
    limited = max(-60.0, min(60.0, float(value) * float(slope)))
    return 1.0 / (1.0 + exp(-limited))


def weighted_mean(weighted_scores: tuple[tuple[float, float], ...], *, default: float = 0.0) -> float:
    total_weight = 0.0
    total = 0.0
    for score, weight in weighted_scores:
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or float(weight) < 0:
            raise ValueError("biodynamic weight must be non-negative numeric")
        numeric_weight = float(weight)
        if numeric_weight <= 0:
            continue
        total += clamp01(score) * numeric_weight
        total_weight += numeric_weight
    if total_weight <= 0:
        return clamp01(default)
    return clamp01(total / total_weight)


def dynamic_threshold(
    base: float,
    *,
    load: float = 0.0,
    drive: float = 0.0,
    recovery: float = 0.0,
    minimum: float = 0.05,
    maximum: float = 0.95,
    load_gain: float = 0.18,
    drive_gain: float = 0.12,
    recovery_gain: float = 0.08,
) -> float:
    """根据压力、驱动和恢复力动态调整阈值。

    压力越高，阈值越谨慎；驱动/恢复力越高，阈值越低摩擦。
    """

    if minimum < 0 or maximum > 1 or minimum > maximum:
        raise ValueError("dynamic_threshold bounds must satisfy 0 <= minimum <= maximum <= 1")
    adjusted = (
        clamp01(base)
        + float(load_gain) * (clamp01(load) - 0.5)
        - float(drive_gain) * (clamp01(drive) - 0.5)
        - float(recovery_gain) * (clamp01(recovery) - 0.5)
    )
    return round(max(float(minimum), min(float(maximum), adjusted)), 4)


def evidence_accumulation(
    *,
    evidence: float,
    drive: float,
    load: float,
    recovery: float = 0.0,
    inertia: float = 0.0,
) -> float:
    """连续证据积累分数。

    evidence/drive/recovery 推高执行倾向；load/inertia 降低执行倾向。
    """

    return clamp01(
        0.38 * clamp01(evidence)
        + 0.30 * clamp01(drive)
        + 0.18 * clamp01(recovery)
        - 0.24 * clamp01(load)
        - 0.10 * clamp01(inertia)
        + 0.20
    )


def activation_probability(score: float, threshold: float, *, softness: float = 0.10) -> float:
    width = max(0.03, min(0.25, float(softness)))
    return clamp01(sigmoid((clamp01(score) - clamp01(threshold)) / width, slope=1.0))


def dynamic_count_requirement(
    base: int,
    *,
    load: float,
    drive: float,
    minimum: int = 1,
    maximum: int = 5,
) -> int:
    if isinstance(base, bool) or not isinstance(base, int):
        raise ValueError("dynamic_count_requirement base must be int")
    raw = float(base) + 1.2 * (clamp01(load) - 0.5) - 0.6 * (clamp01(drive) - 0.5)
    return max(int(minimum), min(int(maximum), int(round(raw))))


@dataclass(frozen=True)
class BioDynamicState:
    """通用动态状态向量。所有字段均为 0..1。"""

    evidence: float = 0.5
    drive: float = 0.5
    resource_pressure: float = 0.0
    failure_pressure: float = 0.0
    uncertainty_pressure: float = 0.0
    privacy_pressure: float = 0.0
    pollution_pressure: float = 0.0
    conflict_pressure: float = 0.0
    fatigue: float = 0.0
    recovery: float = 0.0
    reversibility: float = 0.0
    user_intent: float = 0.0
    inertia: float = 0.0

    def __post_init__(self) -> None:
        for field_name in (
            "evidence",
            "drive",
            "resource_pressure",
            "failure_pressure",
            "uncertainty_pressure",
            "privacy_pressure",
            "pollution_pressure",
            "conflict_pressure",
            "fatigue",
            "recovery",
            "reversibility",
            "user_intent",
            "inertia",
        ):
            clamp01(getattr(self, field_name))

    @property
    def load(self) -> float:
        return weighted_mean(
            (
                (self.resource_pressure, 0.16),
                (self.failure_pressure, 0.16),
                (self.uncertainty_pressure, 0.14),
                (self.privacy_pressure, 0.18),
                (self.pollution_pressure, 0.14),
                (self.conflict_pressure, 0.14),
                (self.fatigue, 0.08),
            )
        )

    @property
    def adaptive_drive(self) -> float:
        return clamp01(0.52 * self.drive + 0.22 * self.user_intent + 0.16 * self.recovery + 0.10 * self.reversibility)

    @property
    def execution_score(self) -> float:
        return evidence_accumulation(
            evidence=self.evidence,
            drive=self.adaptive_drive,
            load=self.load,
            recovery=max(self.recovery, self.reversibility),
            inertia=self.inertia,
        )

    def threshold(self, base: float, *, minimum: float = 0.05, maximum: float = 0.95) -> float:
        return dynamic_threshold(
            base,
            load=self.load,
            drive=self.adaptive_drive,
            recovery=max(self.recovery, self.reversibility),
            minimum=minimum,
            maximum=maximum,
        )

    def probability(self, base_threshold: float, *, minimum: float = 0.05, maximum: float = 0.95) -> float:
        return activation_probability(self.execution_score, self.threshold(base_threshold, minimum=minimum, maximum=maximum))

    def public_dict(self) -> dict[str, float | str]:
        return {
            "schema": L6_72_BIODYNAMIC_POLICY_SCHEMA,
            "evidence": clamp01(self.evidence),
            "drive": clamp01(self.drive),
            "load": self.load,
            "adaptive_drive": self.adaptive_drive,
            "execution_score": self.execution_score,
            "resource_pressure": clamp01(self.resource_pressure),
            "failure_pressure": clamp01(self.failure_pressure),
            "uncertainty_pressure": clamp01(self.uncertainty_pressure),
            "privacy_pressure": clamp01(self.privacy_pressure),
            "pollution_pressure": clamp01(self.pollution_pressure),
            "conflict_pressure": clamp01(self.conflict_pressure),
            "fatigue": clamp01(self.fatigue),
            "recovery": clamp01(self.recovery),
            "reversibility": clamp01(self.reversibility),
            "user_intent": clamp01(self.user_intent),
            "inertia": clamp01(self.inertia),
        }


def bounded_growth(value: float, *, gain: float = 1.0) -> float:
    """类生理饱和曲线：输入越大，边际增益越低。"""

    scaled = max(0.0, float(gain)) * clamp01(value)
    return clamp01(log1p(4.0 * scaled) / log1p(4.0))
