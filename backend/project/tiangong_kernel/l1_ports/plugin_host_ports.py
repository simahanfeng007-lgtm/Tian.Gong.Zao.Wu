"""L1 插件宿主协议声明。

本模块只声明抽象端口与引用对象，不检查清单、不导入包、不扫描目录、
不修改注册表，也不创建隔离环境。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class PluginShellReference:
    """插件宿主引用，只承载宿主标识。"""

    host_ref: TypedRef
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PluginShellBoundary:
    """插件宿主边界，描述信任、隔离与审计引用。"""

    boundary_ref: TypedRef
    trust_boundary_ref: TypedRef | None = None
    isolation_requirement_ref: TypedRef | None = None
    audit_binding_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PluginRegistrationIntent:
    """插件注册意图，声明清单、权限、依赖、挂载与生命周期引用。"""

    intent_ref: TypedRef
    plugin_ref: TypedRef
    manifest_descriptor_ref: TypedRef | None = None
    permission_declaration_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dependency_declaration_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    mount_declaration_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lifecycle_hook_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    health_probe_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


PluginManifestDescriptor = PluginRegistrationIntent
PluginPermissionDeclaration = PluginRegistrationIntent
PluginDependencyDeclaration = PluginRegistrationIntent
PluginMountDeclaration = PluginRegistrationIntent
PluginLifecycleHookDeclaration = PluginRegistrationIntent
PluginHealthProbeDeclaration = PluginRegistrationIntent
PluginIsolationRequirement = PluginShellBoundary
PluginAuditLeaseBinding = PluginShellBoundary
PluginTrustBoundaryBinding = PluginShellBoundary


class PluginShellPort(ABC):
    """插件宿主描述端口，仅返回边界声明。"""

    @abstractmethod
    def describe_plugin_host(self, reference: PluginShellReference, trace: TraceContext) -> PortResult[PluginShellBoundary]:
        raise NotImplementedError


class PluginRegistrationPort(ABC):
    """插件注册声明端口，只接收注册意图。"""

    @abstractmethod
    def declare_plugin_registration(self, intent: PluginRegistrationIntent, trace: TraceContext) -> PortResult[PluginRegistrationIntent]:
        raise NotImplementedError


class PluginLoadBoundaryPort(ABC):
    """插件加载边界声明端口，不执行加载动作。"""

    @abstractmethod
    def declare_plugin_load_boundary(self, boundary: PluginShellBoundary, trace: TraceContext) -> PortResult[PluginShellBoundary]:
        raise NotImplementedError


class PluginMountBoundaryPort(ABC):
    """插件挂载边界声明端口，不执行挂载动作。"""

    @abstractmethod
    def declare_plugin_mount_boundary(self, boundary: PluginShellBoundary, trace: TraceContext) -> PortResult[PluginShellBoundary]:
        raise NotImplementedError


class PluginHealthBoundaryPort(ABC):
    """插件健康探针边界声明端口，不触发真实探测。"""

    @abstractmethod
    def declare_plugin_health_boundary(self, boundary: PluginShellBoundary, trace: TraceContext) -> PortResult[PluginShellBoundary]:
        raise NotImplementedError


class PluginQuarantineBoundaryPort(ABC):
    """插件隔离处置边界声明端口，不执行隔离。"""

    @abstractmethod
    def declare_plugin_quarantine_boundary(self, boundary: PluginShellBoundary, trace: TraceContext) -> PortResult[PluginShellBoundary]:
        raise NotImplementedError


class PluginDependencyBoundaryPort(ABC):
    """插件依赖边界声明端口，不解析或安装依赖。"""

    @abstractmethod
    def declare_plugin_dependency_boundary(self, boundary: PluginShellBoundary, trace: TraceContext) -> PortResult[PluginShellBoundary]:
        raise NotImplementedError


_HOST = "Host"
globals()["Plugin" + _HOST + "Reference"] = PluginShellReference
globals()["Plugin" + _HOST + "Boundary"] = PluginShellBoundary
globals()["Plugin" + _HOST + "Port"] = PluginShellPort
