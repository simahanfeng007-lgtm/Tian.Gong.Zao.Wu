"""L1 第八阶段组件、包、插件 manifest 与注册意图端口协议。

本模块在 L1 中的职责：定义组件引用、组件边界、组件生命周期边界、包引用、包边界、注册意图、注册查询、插件 manifest、插件生命周期边界和插件隔离边界协议。
本模块定义哪些端口：ComponentReferencePort、ComponentBoundaryPort、ComponentLifecycleBoundaryPort、PackageReferencePort、PackageBoundaryPort、RegistryIntentPort、RegistryQueryPort、PluginManifestPort、PluginLifecycleBoundaryPort、PluginIsolationBoundaryPort。
本模块不实现哪些能力：不加载组件、不执行组件、不解包、不安装包、不写注册表、不加载插件、不创建隔离环境。
本模块禁止事项：不得扫描目录、不得读取真实 manifest、不得访问真实注册表、不得加载外部模块。
本模块与 L2-L6 的关系：L2 可记录组件状态，L3 可编排注册意图，L4 可实现包适配，L5 可实现插件宿主外层，L6 可声明子系统 manifest。
本模块如何服务工程生命体：让组件、包和插件先有 manifest 与隔离边界再进入后续层。
本模块如何维持大模型执行力与绝对边界：注册协议只是意图，不阻碍模型使用已释放工具组。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.artifact import ArtifactRef
from tiangong_kernel.l0_primitives.component_package import ComponentBoundaryRef, ComponentInterfaceRef, ComponentRef, ModuleRef, PackageRef, PackageVersionRef
from tiangong_kernel.l0_primitives.environment import SandboxRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef, RegistryRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import VerificationRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult

@dataclass(frozen=True, slots=True)
class ComponentReference:
    """组件引用对象。作用：表达组件引用；边界：不加载组件。"""
    component_ref: ComponentRef
    interface_ref: ComponentInterfaceRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentBoundary:
    """组件边界对象。作用：表达组件边界；边界：不执行组件。"""
    component_ref: ComponentRef = None
    component_boundary_ref: ComponentBoundaryRef | None = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentLifecycleBoundary:
    """组件生命周期边界对象。作用：表达组件生命周期边界；边界：不启动、不停止组件。"""
    component_ref: ComponentRef
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PackageReference:
    """包引用对象。作用：表达包引用；边界：不解包、不安装包。"""
    package_ref: PackageRef
    package_version_ref: PackageVersionRef | None = None
    artifact_ref: ArtifactRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PackageBoundary:
    """包边界对象。作用：表达包边界；边界：不安装、不卸载、不加载。"""
    package_ref: PackageRef = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RegistryIntent:
    """注册意图对象。作用：表达组件或插件注册意图；边界：不写注册表。"""
    registry_ref: RegistryRef
    component_ref: ComponentRef = None
    package_ref: PackageRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RegistryQuery:
    """注册查询对象。作用：表达注册查询协议；边界：不访问真实注册表。"""
    query: QueryEnvelope
    registry_ref: RegistryRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginManifest:
    """插件 manifest 对象。作用：表达插件 manifest 引用；边界：不读取真实 manifest 文件、不加载插件。"""
    manifest_ref: ResourceRef
    namespace_ref: NamespaceRef | None = None
    module_ref: ModuleRef | None = None
    component_ref: ComponentRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginLifecycleBoundary:
    """插件生命周期边界对象。作用：表达插件生命周期边界；边界：不实现插件宿主。"""
    manifest_ref: ResourceRef
    component_ref: ComponentRef = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginIsolationBoundary:
    """插件隔离边界对象。作用：表达插件隔离边界；边界：不创建隔离环境。"""
    manifest_ref: ResourceRef
    sandbox_ref: SandboxRef | None = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentReferenceRequest:
    """ComponentReference请求。作用：提交ComponentReference；边界：只声明组件协议。"""
    payload: ComponentReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentBoundaryRequest:
    """ComponentBoundary请求。作用：提交ComponentBoundary；边界：只声明组件协议。"""
    payload: ComponentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentLifecycleBoundaryRequest:
    """ComponentLifecycleBoundary请求。作用：提交ComponentLifecycleBoundary；边界：只声明组件协议。"""
    payload: ComponentLifecycleBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PackageReferenceRequest:
    """PackageReference请求。作用：提交PackageReference；边界：只声明组件协议。"""
    payload: PackageReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PackageBoundaryRequest:
    """PackageBoundary请求。作用：提交PackageBoundary；边界：只声明组件协议。"""
    payload: PackageBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RegistryIntentRequest:
    """RegistryIntent请求。作用：提交RegistryIntent；边界：只声明组件协议。"""
    payload: RegistryIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RegistryQueryRequest:
    """RegistryQuery请求。作用：提交RegistryQuery；边界：只声明组件协议。"""
    payload: RegistryQuery
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginManifestRequest:
    """PluginManifest请求。作用：提交PluginManifest；边界：只声明组件协议。"""
    payload: PluginManifest
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginLifecycleBoundaryRequest:
    """PluginLifecycleBoundary请求。作用：提交PluginLifecycleBoundary；边界：只声明组件协议。"""
    payload: PluginLifecycleBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginIsolationBoundaryRequest:
    """PluginIsolationBoundary请求。作用：提交PluginIsolationBoundary；边界：只声明组件协议。"""
    payload: PluginIsolationBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentReferenceResponse:
    """ComponentReference响应。作用：返回ComponentReference；边界：不执行组件或插件。"""
    payload: ComponentReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentBoundaryResponse:
    """ComponentBoundary响应。作用：返回ComponentBoundary；边界：不执行组件或插件。"""
    payload: ComponentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ComponentLifecycleBoundaryResponse:
    """ComponentLifecycleBoundary响应。作用：返回ComponentLifecycleBoundary；边界：不执行组件或插件。"""
    payload: ComponentLifecycleBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PackageReferenceResponse:
    """PackageReference响应。作用：返回PackageReference；边界：不执行组件或插件。"""
    payload: PackageReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PackageBoundaryResponse:
    """PackageBoundary响应。作用：返回PackageBoundary；边界：不执行组件或插件。"""
    payload: PackageBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RegistryIntentResponse:
    """RegistryIntent响应。作用：返回RegistryIntent；边界：不执行组件或插件。"""
    payload: RegistryIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RegistryQueryResponse:
    """RegistryQuery响应。作用：返回RegistryQuery；边界：不执行组件或插件。"""
    payload: RegistryQuery
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginManifestResponse:
    """PluginManifest响应。作用：返回PluginManifest；边界：不执行组件或插件。"""
    payload: PluginManifest
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginLifecycleBoundaryResponse:
    """PluginLifecycleBoundary响应。作用：返回PluginLifecycleBoundary；边界：不执行组件或插件。"""
    payload: PluginLifecycleBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PluginIsolationBoundaryResponse:
    """PluginIsolationBoundary响应。作用：返回PluginIsolationBoundary；边界：不执行组件或插件。"""
    payload: PluginIsolationBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class ComponentReferencePort(ABC):
    """组件引用端口。中文名称：组件引用端口。端口职责：定义组件引用协议。输入输出边界：输入 ComponentReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段组件协议。不承担的实现职责：不加载组件。如何服务大模型执行力：让模型可引用组件说明。如何维持绝对边界：引用不执行组件。与后续 L2-L6 的关系：供状态、适配和插件层引用。"""
    @abstractmethod
    def reference_component(self, request: ComponentReferenceRequest, trace: TraceContext) -> PortResult[ComponentReferenceResponse]:
        """声明组件引用端口。"""
        raise NotImplementedError

class ComponentBoundaryPort(ABC):
    """组件边界端口。中文名称：组件边界端口。端口职责：定义组件边界协议。输入输出边界：输入 ComponentBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段组件协议。不承担的实现职责：不执行组件。如何服务大模型执行力：让组件能力有明确边界。如何维持绝对边界：边界不加载组件。与后续 L2-L6 的关系：供插件隔离和外部适配引用。"""
    @abstractmethod
    def describe_component_boundary(self, request: ComponentBoundaryRequest, trace: TraceContext) -> PortResult[ComponentBoundaryResponse]:
        """声明组件边界端口。"""
        raise NotImplementedError

class ComponentLifecycleBoundaryPort(ABC):
    """组件生命周期边界端口。中文名称：组件生命周期边界端口。端口职责：定义组件生命周期边界协议。输入输出边界：输入 ComponentLifecycleBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段组件协议。不承担的实现职责：不启动、不停止组件。如何服务大模型执行力：让组件状态变化可被描述。如何维持绝对边界：生命周期边界不改变状态。与后续 L2-L6 的关系：供 L5 插件外层引用。"""
    @abstractmethod
    def describe_component_lifecycle_boundary(self, request: ComponentLifecycleBoundaryRequest, trace: TraceContext) -> PortResult[ComponentLifecycleBoundaryResponse]:
        """声明组件生命周期边界端口。"""
        raise NotImplementedError

class PackageReferencePort(ABC):
    """包引用端口。中文名称：包引用端口。端口职责：定义包引用协议。输入输出边界：输入 PackageReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段包协议。不承担的实现职责：不解包、不安装。如何服务大模型执行力：让包作为资源引用参与候选链。如何维持绝对边界：引用不加载包。与后续 L2-L6 的关系：供迁移和插件包适配引用。"""
    @abstractmethod
    def reference_package(self, request: PackageReferenceRequest, trace: TraceContext) -> PortResult[PackageReferenceResponse]:
        """声明包引用端口。"""
        raise NotImplementedError

class PackageBoundaryPort(ABC):
    """包边界端口。中文名称：包边界端口。端口职责：定义包边界协议。输入输出边界：输入 PackageBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段包协议。不承担的实现职责：不安装、不卸载、不加载。如何服务大模型执行力：让包变更有边界说明。如何维持绝对边界：边界不改变包状态。与后续 L2-L6 的关系：供外部适配和插件层引用。"""
    @abstractmethod
    def describe_package_boundary(self, request: PackageBoundaryRequest, trace: TraceContext) -> PortResult[PackageBoundaryResponse]:
        """声明包边界端口。"""
        raise NotImplementedError

class RegistryIntentPort(ABC):
    """注册意图端口。中文名称：注册意图端口。端口职责：定义注册意图协议。输入输出边界：输入 RegistryIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段注册协议。不承担的实现职责：不写注册表、不注册插件。如何服务大模型执行力：让新组件先作为候选意图。如何维持绝对边界：意图不写入系统。与后续 L2-L6 的关系：供 L5 注册链引用。"""
    @abstractmethod
    def submit_registry_intent(self, request: RegistryIntentRequest, trace: TraceContext) -> PortResult[RegistryIntentResponse]:
        """声明注册意图端口。"""
        raise NotImplementedError

class RegistryQueryPort(ABC):
    """注册查询端口。中文名称：注册查询端口。端口职责：定义注册查询协议。输入输出边界：输入 RegistryQueryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段注册协议。不承担的实现职责：不访问真实注册表。如何服务大模型执行力：让查询结构可被后续适配。如何维持绝对边界：查询协议不读取数据。与后续 L2-L6 的关系：供插件宿主外层和适配器引用。"""
    @abstractmethod
    def query_registry(self, request: RegistryQueryRequest, trace: TraceContext) -> PortResult[RegistryQueryResponse]:
        """声明注册查询端口。"""
        raise NotImplementedError

class PluginManifestPort(ABC):
    """插件 manifest 端口。中文名称：插件 manifest 端口。端口职责：定义插件 manifest 协议。输入输出边界：输入 PluginManifestRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段插件协议。不承担的实现职责：不读取真实 manifest 文件、不加载插件。如何服务大模型执行力：让插件说明可被边界化。如何维持绝对边界：manifest 协议不执行插件。与后续 L2-L6 的关系：供 L5 和 L6 插件接入引用。"""
    @abstractmethod
    def describe_plugin_manifest(self, request: PluginManifestRequest, trace: TraceContext) -> PortResult[PluginManifestResponse]:
        """声明插件 manifest 端口。"""
        raise NotImplementedError

class PluginLifecycleBoundaryPort(ABC):
    """插件生命周期边界端口。中文名称：插件生命周期边界端口。端口职责：定义插件生命周期边界协议。输入输出边界：输入 PluginLifecycleBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段插件协议。不承担的实现职责：不实现插件宿主。如何服务大模型执行力：让插件状态变化有边界。如何维持绝对边界：边界不启动插件。与后续 L2-L6 的关系：供 L5 外层引用。"""
    @abstractmethod
    def describe_plugin_lifecycle_boundary(self, request: PluginLifecycleBoundaryRequest, trace: TraceContext) -> PortResult[PluginLifecycleBoundaryResponse]:
        """声明插件生命周期边界端口。"""
        raise NotImplementedError

class PluginIsolationBoundaryPort(ABC):
    """插件隔离边界端口。中文名称：插件隔离边界端口。端口职责：定义插件隔离边界协议。输入输出边界：输入 PluginIsolationBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段插件协议。不承担的实现职责：不创建隔离环境。如何服务大模型执行力：让插件可安全扩展。如何维持绝对边界：隔离边界不加载插件。与后续 L2-L6 的关系：供插件宿主外层和安全适配引用。"""
    @abstractmethod
    def describe_plugin_isolation_boundary(self, request: PluginIsolationBoundaryRequest, trace: TraceContext) -> PortResult[PluginIsolationBoundaryResponse]:
        """声明插件隔离边界端口。"""
        raise NotImplementedError
