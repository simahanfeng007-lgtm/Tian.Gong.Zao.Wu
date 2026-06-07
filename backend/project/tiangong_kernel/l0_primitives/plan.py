"""L0 计划事实原语，只表达计划引用、种类、状态、优先级与来源引用；不执行计划、不调度步骤。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId, TypedRef


class PlanKind(str, Enum):
    """PlanKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    SEQUENTIAL = "sequential"
    CHECKLIST = "checklist"
    HIERARCHICAL = "hierarchical"
    DAG = "dag"
    PARALLEL = "parallel"
    NARRATIVE = "narrative"
    PSEUDOCODE = "pseudocode"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class PlanState(str, Enum):
    """PlanState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    REVISING = "revising"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PlanRef:
    """PlanRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: PlanKind = PlanKind.UNKNOWN
    state: PlanState = PlanState.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PlanRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PlanPriority:
    """PlanPriority 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("PlanPriority.value cannot be negative")


@dataclass(frozen=True, slots=True)
class PlanOriginRef:
    """PlanOriginRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: TypedRef
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PlanOriginRef.schema_version cannot be empty")
