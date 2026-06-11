"""L1 端口结果表达。

本模块定义端口调用结果、成功元数据与失败说明，并通过 core_result 字段包裹 L0 CoreResult。
它只表达结果事实，不进行重试、恢复、调度或真实错误处理。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

from tiangong_kernel.l0_primitives.errors import CoreError
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.result import CoreResult, ResultStatus
from tiangong_kernel.l0_primitives.trace import TraceContext


T = TypeVar("T")


class PortResultStatus(str, Enum):
    """端口结果状态枚举；与 L0 ResultStatus 保持可映射关系。"""

    UNKNOWN = "unknown"
    OK = "ok"
    ERROR = "error"
    BOUNDARY_BLOCKED = "boundary_blocked"


@dataclass(frozen=True, slots=True)
class PortSuccessMetadata:
    """端口成功元数据。

    作用：记录端口成功返回时可供后续层引用的轻量事实。
    边界：不采集指标，不写审计，不触发观察回路。
    """

    trace_context: TraceContext | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortSuccessMetadata.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortFailure:
    """端口失败说明。

    作用：表达失败原因、是否与边界有关、可替代路径和证据引用。
    边界：不执行恢复，不决定下一步行动。
    """

    error: CoreError
    is_boundary_related: bool = False
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortFailure.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortResult(Generic[T]):
    """端口结果包装对象。

    作用：让 L1 端口在保留 L0 CoreResult 的同时，补充端口层失败说明与成功元数据。
    边界：只包装结果事实，不吞错、不抛错、不触发真实执行。
    """

    status: PortResultStatus
    core_result: CoreResult[T]
    success_metadata: PortSuccessMetadata | None = None
    failure: PortFailure | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortResult.schema_version cannot be empty")
        if self.status is PortResultStatus.OK and self.core_result.status is not ResultStatus.OK:
            raise ValueError("PortResult OK status requires CoreResult OK status")
        if self.status in {PortResultStatus.ERROR, PortResultStatus.BOUNDARY_BLOCKED}:
            if self.core_result.status is not ResultStatus.ERROR:
                raise ValueError("PortResult failure status requires CoreResult ERROR status")
