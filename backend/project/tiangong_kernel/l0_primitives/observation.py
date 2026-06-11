"""L0 观察事实原语，只表达观察来源、质量、窗口与载荷引用；不采集传感器、网页、文件或模型输出。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId, TypedRef
from .time import TemporalWindow


class ObservationKind(str, Enum):
    """ObservationKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    MESSAGE = "message"
    EVENT = "event"
    STATE = "state"
    EFFECT = "effect"
    METRIC = "metric"
    SIGNAL = "signal"
    CONTENT = "content"
    UNKNOWN = "unknown"


class ObservationQuality(str, Enum):
    """ObservationQuality 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    RAW = "raw"
    PARTIAL = "partial"
    NORMALIZED = "normalized"
    CONFLICTED = "conflicted"
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationRef:
    """ObservationRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ObservationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationWindow:
    """ObservationWindow 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    window: TemporalWindow
    label: str = ""


@dataclass(frozen=True, slots=True)
class ObservationPayloadRef:
    """ObservationPayloadRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    payload_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.payload_type:
            raise ValueError("ObservationPayloadRef.payload_type cannot be empty")
        if not self.schema_version:
            raise ValueError("ObservationPayloadRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ObservationSource:
    """ObservationSource 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    source_ref: TypedRef | None = None
    source_kind: str = "unknown"
    trust_boundary: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.source_kind:
            raise ValueError("ObservationSource.source_kind cannot be empty")
        if not self.trust_boundary:
            raise ValueError("ObservationSource.trust_boundary cannot be empty")
        if not self.schema_version:
            raise ValueError("ObservationSource.schema_version cannot be empty")
