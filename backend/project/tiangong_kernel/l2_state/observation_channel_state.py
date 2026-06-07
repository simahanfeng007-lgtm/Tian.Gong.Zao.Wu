"""L2 观察通道状态对象。

作用：记录观察事实通过哪个外部通道进入状态层及其边界、资源和安全引用。
边界：这是状态对象，不是观察器、采集器或监听器，不实现通道、订阅、传输或队列。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ObservationChannelKind(str, Enum):
    """观察通道类型。

    作用：表达观察事实来自直接状态输入、事件投影、审计投影、指标投影或适配器投影等通道。
    边界：这是状态标签，不打开通道，不订阅、不发布、不消费任何消息。
    """

    DIRECT_STATE_INPUT = "direct_state_input"
    EVENT_PROJECTION = "event_projection"
    AUDIT_PROJECTION = "audit_projection"
    METRIC_PROJECTION = "metric_projection"
    TEST_PROJECTION = "test_projection"
    ADAPTER_PROJECTION = "adapter_projection"
    MANUAL_PROJECTION = "manual_projection"
    UNKNOWN = "unknown"


class ObservationChannelStatus(str, Enum):
    """观察通道状态。

    作用：表达外部报告的通道声明、开放、暂停、中断、关闭、过期或撤销状态。
    边界：这是状态对象的状态标签，不负责打开、关闭或修复通道。
    """

    DECLARED = "declared"
    OPEN = "open"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    CLOSED = "closed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationChannelState:
    """观察通道状态。

    作用：记录通道引用、通道类型、通道状态、观察源、边界、资源、安全和可见范围引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不实现通道、订阅、传输或队列。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    channel_ref: TypedRef | None = None
    channel_kind: ObservationChannelKind = ObservationChannelKind.UNKNOWN
    channel_status: ObservationChannelStatus = ObservationChannelStatus.UNKNOWN
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    expected_observation_kinds: tuple[str, ...] = field(default_factory=tuple)
    visibility_scope_ref: TypedRef | None = None
    latency_label: str | None = None
    throughput_label: str | None = None
    lossiness_label: str | None = None
    ordering_label: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("latency_label", self.latency_label),
            ("throughput_label", self.throughput_label),
            ("lossiness_label", self.lossiness_label),
            ("ordering_label", self.ordering_label),
        ):
            if value == "":
                raise ValueError(f"ObservationChannelState.{name} cannot be empty when provided")
        for value in self.expected_observation_kinds:
            if not value:
                raise ValueError("ObservationChannelState.expected_observation_kinds cannot contain empty values")
        if not self.schema_version:
            raise ValueError("ObservationChannelState.schema_version cannot be empty")
