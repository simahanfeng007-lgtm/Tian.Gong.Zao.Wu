"""L0 信号事实原语，只表达信号类型、强度、极性、置信度与时间窗口；不做打分、推理或触发执行。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId
from .time import TemporalWindow


class SignalKind(str, Enum):
    """SignalKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    HEALTH = "health"
    RESOURCE = "resource"
    RISK = "risk"
    PRESSURE = "pressure"
    FEEDBACK = "feedback"
    RECOVERY = "recovery"
    ADAPTATION = "adaptation"
    DRIFT = "drift"
    DAMAGE = "damage"
    RETENTION = "retention"
    DECAY = "decay"
    REINFORCEMENT = "reinforcement"
    INTERFERENCE = "interference"
    STABILITY = "stability"
    ANOMALY = "anomaly"
    UNKNOWN = "unknown"


class SignalPolarity(str, Enum):
    """SignalPolarity 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SignalRef:
    """SignalRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SignalRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SignalStrength:
    """SignalStrength 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: float

    def __post_init__(self) -> None:
        if self.value < 0.0 or self.value > 1.0:
            raise ValueError("SignalStrength.value must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class SignalConfidence:
    """SignalConfidence 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: float

    def __post_init__(self) -> None:
        if self.value < 0.0 or self.value > 1.0:
            raise ValueError("SignalConfidence.value must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class SignalWindow:
    """SignalWindow 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    window: TemporalWindow
    label: str = ""
