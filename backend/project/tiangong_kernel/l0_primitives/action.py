"""L0 行动意图事实原语，只表达动作引用、类型、状态与意图；不调用工具、不执行动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ActionKind(str, Enum):
    """ActionKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    FINAL = "final"
    ASK_USER = "ask_user"
    REQUEST_EFFECT = "request_effect"
    REFUSE = "refuse"
    NOOP = "noop"
    UNKNOWN = "unknown"


class ActionState(str, Enum):
    """ActionState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ActionRef:
    """ActionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: ActionKind = ActionKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ActionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntent:
    """ActionIntent 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    action_ref: ActionRef
    kind: ActionKind
    state: ActionState = ActionState.PROPOSED
    target_ref: TypedRef | None = None
    reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ActionIntent.schema_version cannot be empty")
