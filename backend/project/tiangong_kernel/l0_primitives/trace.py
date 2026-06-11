"""L0 追踪事实原语，只表达 trace、span、correlation 与 causation 元数据；不采集、不上报、不调度事件。
"""

from __future__ import annotations

from dataclasses import dataclass

from .identity import CoreId, IdPrefix, new_core_id
from .time import SequenceNo


@dataclass(frozen=True, slots=True)
class TraceId:
    """TraceId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: CoreId


@dataclass(frozen=True, slots=True)
class SpanId:
    """SpanId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: CoreId


@dataclass(frozen=True, slots=True)
class CorrelationId:
    """CorrelationId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: CoreId


@dataclass(frozen=True, slots=True)
class CausationId:
    """CausationId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: CoreId


@dataclass(frozen=True, slots=True)
class ActorId:
    """ActorId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: CoreId


@dataclass(frozen=True, slots=True)
class ScopeId:
    """ScopeId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: CoreId


@dataclass(frozen=True, slots=True)
class TraceContext:
    """追踪上下文事实对象。

    TraceContext 只保存 trace/span/correlation 等传播上下文。
    causation_id 归属 CausalEventMetadata，用于表达事件因果链，不在 TraceContext 中重复保存。
    """
    trace_id: TraceId
    span_id: SpanId
    parent_span_id: SpanId | None = None
    correlation_id: CorrelationId | None = None
    actor_id: ActorId | None = None
    scope_id: ScopeId | None = None
    sequence_no: SequenceNo = SequenceNo(0)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("TraceContext.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CausalEventMetadata:
    """事件因果元数据事实对象。

    本对象保存 causation_id，用于表达“当前事件由哪个事实事件触发”的因果引用；不执行回放、恢复或调度。
    """
    trace_id: TraceId
    span_id: SpanId
    parent_span_id: SpanId | None = None
    correlation_id: CorrelationId | None = None
    causation_id: CausationId | None = None
    actor_id: ActorId | None = None
    scope_id: ScopeId | None = None
    sequence_no: SequenceNo = SequenceNo(0)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CausalEventMetadata.schema_version cannot be empty")


def new_trace_context() -> TraceContext:
    return TraceContext(
        trace_id=TraceId(new_core_id(IdPrefix.TRACE)),
        span_id=SpanId(new_core_id(IdPrefix.SPAN)),
    )
