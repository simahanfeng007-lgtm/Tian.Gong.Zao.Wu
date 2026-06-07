"""L1 端口健康声明。

本模块只定义健康状态、健康信号与健康边界的表达形式。
它不探测真实服务、不采集指标、不连接外部系统。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.metric import MetricRef


class PortHealthStatus(str, Enum):
    """端口健康状态枚举；只表达声明性状态。"""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class PortHealthSignal:
    """端口健康信号。

    作用：表达健康相关的事实引用、状态与说明。
    边界：不主动采样，不上报，不改变端口状态。
    """

    status: PortHealthStatus = PortHealthStatus.UNKNOWN
    message: str = ""
    metric_ref: MetricRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortHealthSignal.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortHealthBoundary:
    """端口健康边界。

    作用：说明健康声明的适用范围和不可承诺范围。
    边界：不实现健康检查，不触发降级。
    """

    declared_scope: str
    excluded_scope: str = ""
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.declared_scope:
            raise ValueError("PortHealthBoundary.declared_scope cannot be empty")
        if not self.schema_version:
            raise ValueError("PortHealthBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortHealthDeclaration:
    """端口健康声明。

    作用：汇总端口当前声明性健康状态、健康信号和健康边界。
    边界：不代表实时探活，不连接真实资源。
    """

    status: PortHealthStatus = PortHealthStatus.UNKNOWN
    signals: tuple[PortHealthSignal, ...] = field(default_factory=tuple)
    boundary: PortHealthBoundary | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortHealthDeclaration.schema_version cannot be empty")
