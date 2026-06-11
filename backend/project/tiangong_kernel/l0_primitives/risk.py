"""L0 风险视图事实原语，只表达风险等级、信号与视图；不计算风险分数、不做权限裁决。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class RiskLevel(str, Enum):
    """RiskLevel 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    A0_SAFE = "a0_safe"
    A1_LOW = "a1_low"
    A2_NORMAL = "a2_normal"
    A3_ELEVATED = "a3_elevated"
    A4_REVIEW_REQUIRED = "a4_review_required"
    A5_CRITICAL = "a5_critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RiskRef:
    """RiskRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    level: RiskLevel = RiskLevel.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RiskRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RiskSignal:
    """RiskSignal 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    level: RiskLevel
    source_ref: TypedRef | None = None
    confidence: float = 1.0
    label: str = ""

    def __post_init__(self) -> None:
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("RiskSignal.confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class RiskView:
    """RiskView 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    risk_ref: RiskRef
    level: RiskLevel
    subject_ref: TypedRef | None = None
    signals: tuple[RiskSignal, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RiskView.schema_version cannot be empty")
