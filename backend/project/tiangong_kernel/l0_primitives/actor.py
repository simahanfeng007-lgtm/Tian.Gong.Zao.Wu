"""L0 行为主体引用原语，只表达 actor 的事实类别与引用；不实现 ActorLoop、代理运行或子智能体调度。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId


class ActorKind(str, Enum):
    """ActorKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"
    PLUGIN = "plugin"
    ADAPTER = "adapter"
    SCHEDULER = "scheduler"
    SELF_HEALING = "self_healing"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ActorRef:
    """ActorRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: ActorKind = ActorKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ActorRef.schema_version cannot be empty")
