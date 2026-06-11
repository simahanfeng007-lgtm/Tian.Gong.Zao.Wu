"""L0 时间事实原语，只表达时间戳、时长、窗口、逻辑时钟等不可变值；不读取系统时钟、不调度任务。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClockKind(str, Enum):
    """L0 时钟来源枚举；UNKNOWN 用作无法归类时的稳定兜底。"""

    UNKNOWN = "unknown"
    LOGICAL = "logical"
    WALL = "wall"
    MONOTONIC = "monotonic"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class Timestamp:
    """Timestamp 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    epoch_ms: int

    def __post_init__(self) -> None:
        if self.epoch_ms < 0:
            raise ValueError("Timestamp.epoch_ms cannot be negative")


@dataclass(frozen=True, slots=True)
class Duration:
    """Duration 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    milliseconds: int

    def __post_init__(self) -> None:
        if self.milliseconds < 0:
            raise ValueError("Duration.milliseconds cannot be negative")


@dataclass(frozen=True, slots=True)
class Deadline:
    """Deadline 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    at: Timestamp


@dataclass(frozen=True, slots=True)
class TimeRange:
    """TimeRange 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    start: Timestamp
    end: Timestamp

    def __post_init__(self) -> None:
        if self.end.epoch_ms < self.start.epoch_ms:
            raise ValueError("TimeRange.end cannot be earlier than start")


@dataclass(frozen=True, slots=True)
class TemporalWindow:
    """TemporalWindow 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    range: TimeRange
    label: str = ""


@dataclass(frozen=True, slots=True)
class SequenceNo:
    """SequenceNo 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("SequenceNo.value cannot be negative")


@dataclass(frozen=True, slots=True)
class LogicalTime:
    """LogicalTime 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    tick: SequenceNo
    lane: str = "default"

    def __post_init__(self) -> None:
        if not self.lane:
            raise ValueError("LogicalTime.lane cannot be empty")


@dataclass(frozen=True, slots=True)
class LogicalClock:
    """LogicalClock 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    current: LogicalTime


@dataclass(frozen=True, slots=True)
class ClockSourceRef:
    """ClockSourceRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str
    kind: ClockKind = ClockKind.LOGICAL

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ClockSourceRef.value cannot be empty")
