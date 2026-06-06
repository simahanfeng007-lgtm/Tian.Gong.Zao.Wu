"""L1 环境端口协议。

本模块在 L1 中的职责：定义环境、沙箱、位置解析、运行上下文与环境观察端口协议。
本模块定义：EnvironmentPort、SandboxPort、LocationResolverPort、RuntimeContextPort、EnvironmentObservationPort。
本模块不实现：真实环境变量读取、真实机器探测、真实沙箱启动、真实路径解析、真实运行时创建或环境采集。
本模块禁止事项：不得访问文件系统、网络、进程、环境变量、外部定位系统、真实模型或真实工具。
本模块与 L2-L6 的关系：L2 可记录环境状态，L3 可组织环境边界，L4 可实现外部适配，L5 可隔离插件环境，L6 可提交子系统环境观察事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import PayloadRef
from tiangong_kernel.l0_primitives.environment import EnvironmentRef, SandboxRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.location import LocationRef, ResolutionHintRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class EnvironmentPortBoundary:
    """环境端口边界对象。

    作用：表达环境、沙箱、位置、运行上下文与环境观察的协议边界。
    边界：只描述环境界限，不探测真实机器，不创建真实运行时。
    """

    boundary: PortBoundary
    environment_ref: EnvironmentRef | None = None
    sandbox_ref: SandboxRef | None = None
    location_ref: LocationRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EnvironmentDescribeRequest:
    """环境描述请求。

    作用：声明需要描述的环境引用、范围与结构版本。
    边界：不读取真实系统环境变量，不探测真实机器。
    """

    environment_ref: EnvironmentRef
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EnvironmentDescribeResponse:
    """环境描述响应。

    作用：承载环境引用、范围引用、载荷引用和证据引用。
    边界：不代表已经采集真实环境，不暴露环境变量。
    """

    environment_ref: EnvironmentRef
    scope_ref: ScopeRef | None = None
    payload_ref: PayloadRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SandboxBoundaryRequest:
    """沙箱边界请求。

    作用：声明沙箱引用、环境引用和资源引用之间的边界关系。
    边界：不启动隔离环境，不启动进程，不分配真实资源。
    """

    sandbox_ref: SandboxRef
    environment_ref: EnvironmentRef | None = None
    resource_ref: ResourceRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SandboxBoundaryResponse:
    """沙箱边界响应。

    作用：承载沙箱引用、环境引用、资源引用和审计引用。
    边界：不代表沙箱已启动，不保证隔离已经建立。
    """

    sandbox_ref: SandboxRef
    environment_ref: EnvironmentRef | None = None
    resource_ref: ResourceRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LocationResolveRequest:
    """位置解析请求。

    作用：声明位置引用、解析提示与环境边界之间的协议关系。
    边界：不读取真实路径，不访问地理位置，不扫描文件系统。
    """

    location_ref: LocationRef
    resolution_hint_ref: ResolutionHintRef | None = None
    environment_ref: EnvironmentRef | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LocationResolveResponse:
    """位置解析响应。

    作用：承载解析后的可引用位置、环境引用与证据引用。
    边界：不暴露真实路径字符串，不访问外部定位系统。
    """

    location_ref: LocationRef
    environment_ref: EnvironmentRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RuntimeContextDeclareRequest:
    """运行上下文声明请求。

    作用：声明环境、沙箱、资源、位置与范围组成的运行上下文边界。
    边界：不创建真实运行时，不调度任务，不启动循环。
    """

    environment_ref: EnvironmentRef | None = None
    sandbox_ref: SandboxRef | None = None
    resource_ref: ResourceRef | None = None
    location_ref: LocationRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RuntimeContextDeclareResponse:
    """运行上下文声明响应。

    作用：承载运行上下文边界中的环境、沙箱、资源与位置引用。
    边界：不代表真实运行时已创建，不触发执行。
    """

    environment_ref: EnvironmentRef | None = None
    sandbox_ref: SandboxRef | None = None
    resource_ref: ResourceRef | None = None
    location_ref: LocationRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EnvironmentObservationRequest:
    """环境观察请求。

    作用：声明环境观察引用、环境引用、信号引用与载荷引用之间的关系。
    边界：不采集真实环境，不读取机器状态，不上报遥测。
    """

    observation_ref: ObservationRef
    environment_ref: EnvironmentRef | None = None
    sandbox_ref: SandboxRef | None = None
    signal_ref: SignalRef | None = None
    payload_ref: PayloadRef | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EnvironmentObservationResponse:
    """环境观察响应。

    作用：承载环境观察引用、环境引用、信号引用与证据引用。
    边界：不代表真实采集已发生，不触发外部上报。
    """

    observation_ref: ObservationRef
    environment_ref: EnvironmentRef | None = None
    signal_ref: SignalRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class EnvironmentPort(ABC):
    """环境端口。

    中文名称：环境描述端口。
    端口职责：定义环境引用和环境边界的 L1 协议。
    输入输出边界：输入 EnvironmentDescribeRequest 与 TraceContext，输出 PortResult 包装的 EnvironmentDescribeResponse。
    所属 L1 层：环境端口协议。
    不承担的实现职责：不读取真实系统环境变量，不探测真实机器。
    """

    @abstractmethod
    def describe_environment(
        self, request: EnvironmentDescribeRequest, trace: TraceContext
    ) -> PortResult[EnvironmentDescribeResponse]:
        """声明环境描述协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_environment_boundary(self, trace: TraceContext) -> CoreResult[EnvironmentPortBoundary]:
        """声明环境边界说明协议。"""
        raise NotImplementedError


class SandboxPort(ABC):
    """沙箱端口。

    中文名称：沙箱边界端口。
    端口职责：定义沙箱引用和沙箱边界的 L1 协议。
    输入输出边界：输入 SandboxBoundaryRequest 与 TraceContext，输出 PortResult 包装的 SandboxBoundaryResponse。
    所属 L1 层：环境端口协议。
    不承担的实现职责：不启动隔离环境，不启动进程，不分配真实资源。
    """

    @abstractmethod
    def declare_sandbox_boundary(
        self, request: SandboxBoundaryRequest, trace: TraceContext
    ) -> PortResult[SandboxBoundaryResponse]:
        """声明沙箱边界协议。"""
        raise NotImplementedError


class LocationResolverPort(ABC):
    """位置解析端口。

    中文名称：位置解析端口。
    端口职责：定义位置引用和位置解析边界的 L1 协议。
    输入输出边界：输入 LocationResolveRequest 与 TraceContext，输出 PortResult 包装的 LocationResolveResponse。
    所属 L1 层：环境端口协议。
    不承担的实现职责：不读取真实路径，不访问地理位置，不扫描文件系统。
    """

    @abstractmethod
    def resolve_location(self, request: LocationResolveRequest, trace: TraceContext) -> PortResult[LocationResolveResponse]:
        """声明位置解析协议。"""
        raise NotImplementedError


class RuntimeContextPort(ABC):
    """运行上下文端口。

    中文名称：运行上下文边界端口。
    端口职责：定义运行上下文边界的 L1 协议。
    输入输出边界：输入 RuntimeContextDeclareRequest 与 TraceContext，输出 PortResult 包装的 RuntimeContextDeclareResponse。
    所属 L1 层：环境端口协议。
    不承担的实现职责：不创建真实运行时，不调度任务，不启动循环。
    """

    @abstractmethod
    def declare_runtime_context(
        self, request: RuntimeContextDeclareRequest, trace: TraceContext
    ) -> PortResult[RuntimeContextDeclareResponse]:
        """声明运行上下文边界协议。"""
        raise NotImplementedError


class EnvironmentObservationPort(ABC):
    """环境观察端口。

    中文名称：环境观察端口。
    端口职责：定义环境观察结果的 L1 协议。
    输入输出边界：输入 EnvironmentObservationRequest 与 TraceContext，输出 PortResult 包装的 EnvironmentObservationResponse。
    所属 L1 层：环境端口协议。
    不承担的实现职责：不采集真实环境，不读取机器状态，不上报遥测。
    """

    @abstractmethod
    def submit_environment_observation(
        self, request: EnvironmentObservationRequest, trace: TraceContext
    ) -> PortResult[EnvironmentObservationResponse]:
        """声明环境观察提交协议。"""
        raise NotImplementedError
