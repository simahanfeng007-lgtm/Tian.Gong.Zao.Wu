"""L1 通用请求、响应、命令与查询信封。

本模块定义端口间传递信息的稳定包装对象，供后续 L2-L6 引用。
信封只携带引用、载荷和值对象，不携带真实资源句柄，也不触发任何外部动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.trace import TraceContext

from .base import PortIdentity
from .port_boundary import BoundaryViolation, PortBoundary


class EnvelopeKind(str, Enum):
    """信封类型枚举；只表达传递语义。"""

    REQUEST = "request"
    RESPONSE = "response"
    COMMAND = "command"
    QUERY = "query"


@dataclass(frozen=True, slots=True)
class PortCallMetadata:
    """端口调用元数据。

    作用：保存追踪上下文、调用方引用、目标端口引用和证据引用。
    边界：不采集、不上报、不生成外部日志。
    """

    trace_context: TraceContext | None = None
    caller_ref: TypedRef | None = None
    target_port: PortIdentity | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortCallMetadata.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortBoundaryContext:
    """端口边界上下文。

    作用：在请求或响应中携带边界说明、越界事实与替代路径。
    边界：不执行边界判断，不替调用方规划下一步。
    """

    boundary: PortBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortBoundaryContext.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortRequest:
    """端口请求信封。

    作用：表达一次端口请求的身份、目标、载荷、元数据与边界上下文。
    边界：不验证业务、不调用端口、不承载真实资源句柄。
    """

    request_id: RefId
    target_port: PortIdentity
    payload: Any = None
    metadata: PortCallMetadata | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortResponse:
    """端口响应信封。

    作用：表达一次端口响应的身份、对应请求、结果、元数据与边界上下文。
    边界：不解释业务结果，不触发恢复，不调度后续动作。
    """

    response_id: RefId
    request_id: RefId
    result: CoreResult[Any]
    metadata: PortCallMetadata | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CommandEnvelope:
    """命令信封。

    作用：表达后续执行面可能使用的命令式请求包装。
    边界：不执行命令，不改变状态，不释放工具组。
    """

    command_id: RefId
    request: PortRequest
    command_name: str
    parameters: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    metadata: PortCallMetadata | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.command_name:
            raise ValueError("CommandEnvelope.command_name cannot be empty")
        if not self.schema_version:
            raise ValueError("CommandEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class QueryEnvelope:
    """查询信封。

    作用：表达后续观察面或控制面可能使用的查询式请求包装。
    边界：不查询真实资源，不读取文件、网络或数据库。
    """

    query_id: RefId
    request: PortRequest
    query_name: str
    criteria: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    metadata: PortCallMetadata | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.query_name:
            raise ValueError("QueryEnvelope.query_name cannot be empty")
        if not self.schema_version:
            raise ValueError("QueryEnvelope.schema_version cannot be empty")
