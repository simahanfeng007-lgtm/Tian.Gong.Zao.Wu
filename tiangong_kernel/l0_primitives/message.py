"""L0 消息事实原语，只表达消息角色、状态、内容引用与相关引用；不构造 prompt、不调用模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .content import ContentRef
from .identity import RefId, TypedRef
from .time import Timestamp
from .trace import CausalEventMetadata


class MessageRole(str, Enum):
    """MessageRole 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    EFFECT = "effect"
    EVENT = "event"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class MessageState(str, Enum):
    """MessageState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    CREATED = "created"
    RECORDED = "recorded"
    SUPERSEDED = "superseded"
    REDACTED = "redacted"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MessageRef:
    """MessageRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MessageRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CoreMessage:
    """CoreMessage 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    message_ref: MessageRef
    role: MessageRole
    state: MessageState
    created_at: Timestamp
    trace: CausalEventMetadata
    content_ref: ContentRef | None = None
    origin_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = ()
    schema_version: str = "0.1"
    labels: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CoreMessage.schema_version cannot be empty")
        if any(not label for label in self.labels):
            raise ValueError("CoreMessage.labels cannot contain empty values")
