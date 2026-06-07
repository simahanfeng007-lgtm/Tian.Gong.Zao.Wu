"""L1 端口基础协议。

本模块只定义端口身份、分类、方向、内部可见性与抽象端口协议。
它服务于后续 L2-L6 对端口的统一引用，不承载真实资源句柄、不进行调度、不调用模型或工具。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.result import CoreResult


@dataclass(frozen=True, slots=True)
class PortName:
    """端口名称值对象。

    作用：为 L1 端口提供稳定、可读、不可变的名称。
    边界：只保存名称事实，不负责注册、查找或调度。
    """

    value: str
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("PortName.value cannot be empty")
        if not self.schema_version:
            raise ValueError("PortName.schema_version cannot be empty")


class PortKind(str, Enum):
    """端口类别枚举；只表达端口所属公共类别。"""

    UNKNOWN = "unknown"
    CONTROL = "control"
    EXECUTION = "execution"
    OBSERVATION = "observation"
    CONTENT = "content"
    COMMUNICATION = "communication"
    ENVIRONMENT = "environment"
    ADAPTER = "adapter"


class PortPlane(str, Enum):
    """三面结构枚举：控制面、执行面、观察面。"""

    CONTROL = "control"
    EXECUTION = "execution"
    OBSERVATION = "observation"


class PortDirection(str, Enum):
    """端口方向枚举；只表达调用方向，不启动任何调用。"""

    UNKNOWN = "unknown"
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class PortVisibility(str, Enum):
    """端口内部可见性枚举；只用于系统内部协议，不代表大模型可见。"""

    INTERNAL = "internal"
    LAYER_PUBLIC = "layer_public"
    IMPLEMENTER_ONLY = "implementer_only"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class PortIdentity:
    """端口身份声明。

    作用：稳定表达一个 L1 端口的身份、类别、三面归属、方向与内部可见性。
    边界：不创建端口实例，不注册端口，不暴露给大模型作为操作对象。
    """

    port_id: RefId
    name: PortName
    kind: PortKind = PortKind.UNKNOWN
    plane: PortPlane = PortPlane.CONTROL
    direction: PortDirection = PortDirection.UNKNOWN
    visibility: PortVisibility = PortVisibility.INTERNAL
    source_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortIdentity.schema_version cannot be empty")


class BasePort(ABC):
    """L1 基础端口抽象协议。

    作用：规定端口必须声明身份、边界、健康、生命周期，并以 CoreResult 返回协议结果。
    边界：这里只定义抽象方法，不提供真实端口能力，不接触外部资源。
    """

    @property
    @abstractmethod
    def identity(self) -> PortIdentity:
        """返回端口身份声明。"""
        raise NotImplementedError

    @abstractmethod
    def describe_boundary(self) -> CoreResult[object]:
        """返回端口边界说明。"""
        raise NotImplementedError

    @abstractmethod
    def describe_health(self) -> CoreResult[object]:
        """返回端口健康声明。"""
        raise NotImplementedError

    @abstractmethod
    def describe_lifecycle(self) -> CoreResult[object]:
        """返回端口生命周期声明。"""
        raise NotImplementedError
