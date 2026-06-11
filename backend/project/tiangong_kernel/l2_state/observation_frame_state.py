"""L2 观察帧状态对象。

作用：记录一次外部观察事实的结构化快照及其来源、通道、质量、边界和安全引用。
边界：这是状态对象，不是观察器、采集器或监听器，不解析真实日志、模型输出或工具结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ObservationFrameKind(str, Enum):
    """观察帧类型。

    作用：表达观察帧记录事件、指标、审计、效果、模型反馈、边界、安全、资源或环境事实。
    边界：这是状态标签，不解析真实日志、模型输出、工具结果或外部 payload。
    """

    EVENT = "event"
    METRIC = "metric"
    AUDIT = "audit"
    EFFECT = "effect"
    MODEL_FEEDBACK = "model_feedback"
    BOUNDARY = "boundary"
    SECURITY = "security"
    RESOURCE = "resource"
    ENVIRONMENT = "environment"
    TEST = "test"
    SUMMARY = "summary"
    UNKNOWN = "unknown"


class ObservationFrameStatus(str, Enum):
    """观察帧状态。

    作用：表达观察帧已捕获、已接受、已脱敏、部分、冲突、过期、丢弃或未知状态。
    边界：这是状态对象的状态标签，不决定观察是否可用，不触发候选或恢复。
    """

    CAPTURED = "captured"
    ACCEPTED = "accepted"
    REDACTED = "redacted"
    PARTIAL = "partial"
    CONFLICTED = "conflicted"
    STALE = "stale"
    DISCARDED = "discarded"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationFrameState:
    """观察帧状态。

    作用：记录观察帧引用、来源、通道、被观察对象、短摘要、payload 引用、质量、边界和安全引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不保存真实敏感 payload，不解析真实输出。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    frame_ref: TypedRef | None = None
    frame_kind: ObservationFrameKind = ObservationFrameKind.UNKNOWN
    frame_status: ObservationFrameStatus = ObservationFrameStatus.UNKNOWN
    source_state_ref: TypedRef | None = None
    channel_state_ref: TypedRef | None = None
    observed_subject_ref: TypedRef | None = None
    observed_subject_kind: str | None = None
    observed_status: str | None = None
    observed_summary: str | None = None
    observed_payload_ref: TypedRef | None = None
    quality_state_ref: TypedRef | None = None
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    timestamp_ref: TypedRef | None = None
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    related_skill_ref: TypedRef | None = None
    related_tool_group_ref: TypedRef | None = None
    related_tool_intent_ref: TypedRef | None = None
    related_action_ref: TypedRef | None = None
    related_effect_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("observed_subject_kind", self.observed_subject_kind),
            ("observed_status", self.observed_status),
            ("observed_summary", self.observed_summary),
        ):
            if value == "":
                raise ValueError(f"ObservationFrameState.{name} cannot be empty when provided")
        if self.observed_summary is not None and len(self.observed_summary) > 512:
            raise ValueError("ObservationFrameState.observed_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ObservationFrameState.schema_version cannot be empty")
