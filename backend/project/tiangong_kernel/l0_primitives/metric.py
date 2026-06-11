"""L0 指标事实原语，只表达指标名、单位、值、窗口与聚合类型；不采样、不统计、不上报。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId
from .time import TemporalWindow, Timestamp


class MetricKind(str, Enum):
    """MetricKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    LATENCY = "latency"
    COUNT = "count"
    RATE = "rate"
    RATIO = "ratio"
    SIZE = "size"
    CAPACITY = "capacity"
    USAGE = "usage"
    ERROR = "error"
    THROUGHPUT = "throughput"
    COST = "cost"
    QUALITY = "quality"
    CONFIDENCE = "confidence"
    UNKNOWN = "unknown"


class MetricAggregation(str, Enum):
    """MetricAggregation 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    POINT = "point"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MetricRef:
    """MetricRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MetricRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MetricValue:
    """MetricValue 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: int | float


@dataclass(frozen=True, slots=True)
class MetricUnit:
    """MetricUnit 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MetricUnit.value cannot be empty")


@dataclass(frozen=True, slots=True)
class MetricWindow:
    """MetricWindow 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    window: TemporalWindow
    label: str = ""


@dataclass(frozen=True, slots=True)
class MetricPoint:
    """MetricPoint 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    metric_ref: MetricRef
    kind: MetricKind
    value: MetricValue
    unit: MetricUnit
    observed_at: Timestamp
    aggregation: MetricAggregation = MetricAggregation.POINT


@dataclass(frozen=True, slots=True)
class MetricSeriesRef:
    """MetricSeriesRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    metric_kind: MetricKind = MetricKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MetricSeriesRef.schema_version cannot be empty")
