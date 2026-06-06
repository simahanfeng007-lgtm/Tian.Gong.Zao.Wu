"""L0 目标事实原语，只表达目标引用、优先级、状态与成功/失败条件引用；不规划、不优化、不推进目标。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId


class GoalKind(str, Enum):
    """GoalKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    USER_REQUEST = "user_request"
    SYSTEM_MAINTENANCE = "system_maintenance"
    RECOVERY = "recovery"
    LEARNING = "learning"
    EXPLORATION = "exploration"
    SAFETY = "safety"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class GoalState(str, Enum):
    """GoalState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GoalRef:
    """GoalRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: GoalKind = GoalKind.UNKNOWN
    state: GoalState = GoalState.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("GoalRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class GoalPriority:
    """GoalPriority 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("GoalPriority.value cannot be negative")


@dataclass(frozen=True, slots=True)
class GoalSuccessCriteriaRef:
    """GoalSuccessCriteriaRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("GoalSuccessCriteriaRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class GoalFailureCriteriaRef:
    """GoalFailureCriteriaRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("GoalFailureCriteriaRef.schema_version cannot be empty")
