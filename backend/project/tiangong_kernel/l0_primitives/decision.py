"""L0 裁决事实原语，只记录外部裁决的事实形态；不实现 allow/deny 策略算法。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef
from .time import Timestamp


class DecisionKind(str, Enum):
    """DecisionKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    ALLOW = "allow"
    WARN = "warn"
    REVIEW = "review"
    BLOCK = "block"
    DEFER = "defer"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DecisionRef:
    """DecisionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: DecisionKind = DecisionKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("DecisionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DecisionReason:
    """DecisionReason 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    code: str
    message: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("DecisionReason.code cannot be empty")


@dataclass(frozen=True, slots=True)
class Decision:
    """Decision 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    decision_ref: DecisionRef
    kind: DecisionKind
    decided_at: Timestamp
    reason: DecisionReason | None = None
    subject_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("Decision.schema_version cannot be empty")
