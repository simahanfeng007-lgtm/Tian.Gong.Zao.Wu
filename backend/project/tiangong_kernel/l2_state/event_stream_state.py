"""L2 事件流状态对象。

作用：记录外部报告的事件流类型、状态、帧计数、中断和截断引用。
边界：这是状态对象，不是观察器、采集器或监听器，不实现事件总线、网络流或队列消费。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class EventStreamKind(str, Enum):
    """事件流类型。

    作用：表达外部报告的运行、任务、模型、工具、边界、资源、审计或测试事件流标签。
    边界：这是状态标签，不实现事件总线、网络流或队列消费。
    """

    RUN_EVENT_STREAM = "run_event_stream"
    TASK_EVENT_STREAM = "task_event_stream"
    MODEL_EVENT_STREAM = "model_event_stream"
    TOOL_EVENT_STREAM = "tool_event_stream"
    BOUNDARY_EVENT_STREAM = "boundary_event_stream"
    RESOURCE_EVENT_STREAM = "resource_event_stream"
    AUDIT_EVENT_STREAM = "audit_event_stream"
    TEST_EVENT_STREAM = "test_event_stream"
    UNKNOWN = "unknown"


class EventStreamStatus(str, Enum):
    """事件流状态。

    作用：表达外部报告的事件流声明、开放、传输中、空闲、中断、截断、关闭、过期或失败状态。
    边界：这是状态对象的状态标签，不打开连接，不消费真实事件。
    """

    DECLARED = "declared"
    OPEN = "open"
    STREAMING = "streaming"
    IDLE = "idle"
    INTERRUPTED = "interrupted"
    TRUNCATED = "truncated"
    CLOSED = "closed"
    EXPIRED = "expired"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EventStreamState:
    """事件流状态。

    作用：记录事件流引用、来源、通道、最新帧、帧计数、中断、截断和相关运行任务引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不实现事件总线、网络流或队列消费。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    stream_ref: TypedRef | None = None
    stream_kind: EventStreamKind = EventStreamKind.UNKNOWN
    stream_status: EventStreamStatus = EventStreamStatus.UNKNOWN
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    channel_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    latest_frame_ref: TypedRef | None = None
    frame_count: int = 0
    dropped_frame_count: int = 0
    redacted_frame_count: int = 0
    interruption_reason_ref: TypedRef | None = None
    truncation_reason_ref: TypedRef | None = None
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("frame_count", self.frame_count),
            ("dropped_frame_count", self.dropped_frame_count),
            ("redacted_frame_count", self.redacted_frame_count),
        ):
            if value < 0:
                raise ValueError(f"EventStreamState.{name} cannot be negative")
        if not self.schema_version:
            raise ValueError("EventStreamState.schema_version cannot be empty")
