"""L0 事件事实原语，只表达事件引用、事件类型、事件元数据与载荷引用；不实现 EventStore、dispatch 或事件总线。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef
from .time import Timestamp
from .trace import CausalEventMetadata


class EventType(str, Enum):
    """EventType 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    RUN_CREATED = "run_created"
    STATE_CHANGED = "state_changed"
    MESSAGE_ADDED = "message_added"
    ACTION_PROPOSED = "action_proposed"
    DECISION_RECORDED = "decision_recorded"
    EFFECT_REQUESTED = "effect_requested"
    EFFECT_ACCEPTED = "effect_accepted"
    EFFECT_REJECTED = "effect_rejected"
    CHECKPOINT_CREATED = "checkpoint_created"
    ERROR_RAISED = "error_raised"
    LIFECYCLE_CHANGED = "lifecycle_changed"
    SIGNAL_RECORDED = "signal_recorded"
    METRIC_RECORDED = "metric_recorded"
    RUN_CLOSED = "run_closed"
    UNKNOWN = "unknown"


class EventState(str, Enum):
    """EventState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    RECORDED = "recorded"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EventRef:
    """EventRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EventRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EventPayloadRef:
    """EventPayloadRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    payload_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.payload_type:
            raise ValueError("EventPayloadRef.payload_type cannot be empty")
        if not self.schema_version:
            raise ValueError("EventPayloadRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EventMeta:
    """EventMeta 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    schema_version: str = "0.1"
    origin_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = ()
    tags: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EventMeta.schema_version cannot be empty")
        if any(not tag for tag in self.tags):
            raise ValueError("EventMeta.tags cannot contain empty values")
        if any(not key for key, _ in self.attributes):
            raise ValueError("EventMeta.attributes keys cannot be empty")


@dataclass(frozen=True, slots=True)
class CoreEvent:
    """CoreEvent 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    event_ref: EventRef
    event_type: EventType
    state: EventState
    created_at: Timestamp
    trace: CausalEventMetadata
    payload_ref: EventPayloadRef | None = None
    meta: EventMeta = field(default_factory=EventMeta)
