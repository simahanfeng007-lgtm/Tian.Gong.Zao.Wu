"""L2 观察指标状态对象。

作用：记录外部已经给出的指标快照及其资源、运行、任务和质量引用。
边界：这是状态对象，不是观察器、采集器或监听器，不采样、不统计、不扣减配额。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ObservationMetricKind(str, Enum):
    """观察指标类型。

    作用：表达计数、耗时、延迟、吞吐、错误率、成功率、资源压力或质量信号等指标标签。
    边界：这是状态标签，不采样系统指标，不做统计计算或预算扣减。
    """

    COUNT = "count"
    DURATION = "duration"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    TOKEN_USAGE = "token_usage"
    BUDGET_USAGE = "budget_usage"
    RESOURCE_PRESSURE = "resource_pressure"
    HEALTH_SIGNAL = "health_signal"
    QUALITY_SIGNAL = "quality_signal"
    UNKNOWN = "unknown"


class ObservationMetricStatus(str, Enum):
    """观察指标状态。

    作用：表达外部报告、估计、部分、过期、脱敏、冲突或未知的指标状态。
    边界：这是状态对象的状态标签，不判断指标质量，不触发资源扣减。
    """

    REPORTED = "reported"
    ESTIMATED = "estimated"
    PARTIAL = "partial"
    STALE = "stale"
    REDACTED = "redacted"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationMetricState:
    """观察指标状态。

    作用：记录指标引用、类型、状态、名称、值表示、单位、窗口、来源、通道、资源和质量引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不采样、不统计、不扣减配额。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    metric_ref: TypedRef | None = None
    metric_kind: ObservationMetricKind = ObservationMetricKind.UNKNOWN
    metric_status: ObservationMetricStatus = ObservationMetricStatus.UNKNOWN
    metric_name: str | None = None
    metric_value_repr: str | None = None
    metric_unit: str | None = None
    metric_window_ref: TypedRef | None = None
    source_state_ref: TypedRef | None = None
    channel_state_ref: TypedRef | None = None
    related_resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    quality_state_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("metric_name", self.metric_name),
            ("metric_value_repr", self.metric_value_repr),
            ("metric_unit", self.metric_unit),
        ):
            if value == "":
                raise ValueError(f"ObservationMetricState.{name} cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ObservationMetricState.schema_version cannot be empty")
