"""L1 基础设施端口协议。

本模块在 L1 中的职责：定义时间、标识、序列化、摘要与日志提交的基础设施端口。
本模块定义：ClockPort、IdGeneratorPort、SerializationPort、HashPort、LoggerPort。
本模块不实现：真实时间读取、真实标识算法、真实序列化器、真实摘要计算、真实日志写入。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实环境、模型或工具。
本模块与 L2-L6 的关系：L2 可引用时间与标识来源，L3 可声明基础设施依赖，L4 可在外部适配层实现协议，L5 可记录插件健康，L6 可提交子系统日志事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.event import EventRef
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.time import ClockSourceRef, LogicalTime, Timestamp
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class InfrastructurePortBoundary:
    """基础设施端口边界对象。

    作用：统一说明本组端口的 L1 边界、适用范围和证据引用。
    边界：只描述协议边界，不实现基础设施能力，不替上层选择实现。
    """

    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ClockQueryRequest:
    """时间查询请求。

    作用：声明调用方需要一个时间事实或逻辑时钟事实。
    边界：不读取系统时间，不启动定时器，不做调度。
    """

    clock_source_ref: ClockSourceRef | None = None
    scope_ref: ScopeRef | None = None
    actor_ref: ActorRef | None = None
    schema_ref: SchemaRef | None = None
    metadata_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ClockQueryResponse:
    """时间查询响应。

    作用：承载实现方返回的时间值或逻辑时间值。
    边界：不证明时间来源真实性，不进行时间同步。
    """

    timestamp: Timestamp | None = None
    logical_time: LogicalTime | None = None
    clock_source_ref: ClockSourceRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IdGenerationRequest:
    """标识生成请求。

    作用：声明需要一个特定命名空间内的稳定引用标识。
    边界：不定义或实现标识生成算法，不访问注册表。
    """

    namespace_ref: NamespaceRef
    scope_ref: ScopeRef | None = None
    actor_ref: ActorRef | None = None
    seed_payload_ref: PayloadRef | None = None
    schema_ref: SchemaRef | None = None
    metadata_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class IdGenerationResponse:
    """标识生成响应。

    作用：承载实现方生成的 L0 RefId 事实。
    边界：不校验全局唯一性，不保存标识分配记录。
    """

    generated_ref_id: RefId
    namespace_ref: NamespaceRef
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SerializationRequest:
    """序列化请求。

    作用：声明某个载荷或内容需要被转为稳定表达。
    边界：不实现真实序列化算法，不读取或写入任何资源。
    """

    payload_ref: PayloadRef | None = None
    content_ref: ContentRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    metadata_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SerializationResponse:
    """序列化响应。

    作用：承载序列化结果的内容引用或载荷引用。
    边界：不包含真实字节内容，不落盘，不上传。
    """

    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    schema_ref: SchemaRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DeserializationRequest:
    """反序列化请求。

    作用：声明某个内容引用需要被恢复为协议载荷引用。
    边界：不构造上层对象，不访问真实资源，不执行反射工厂。
    """

    content_ref: ContentRef
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    metadata_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DeserializationResponse:
    """反序列化响应。

    作用：承载反序列化后的载荷引用或内容引用。
    边界：不返回裸对象，不实例化后续层实体。
    """

    payload_ref: PayloadRef | None = None
    content_ref: ContentRef | None = None
    schema_ref: SchemaRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class HashRequest:
    """摘要请求。

    作用：声明某个内容、载荷或资源需要摘要事实。
    边界：不实现摘要算法，不读取真实内容，不执行密码学流程。
    """

    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    resource_ref: ResourceRef | None = None
    schema_ref: SchemaRef | None = None
    metadata_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class HashResponse:
    """摘要响应。

    作用：承载摘要事实的证据引用。
    边界：不暴露摘要字符串，不声明加密强度。
    """

    evidence_ref: EvidenceRef
    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    resource_ref: ResourceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LogSubmitRequest:
    """日志提交请求。

    作用：声明需要提交的日志事实引用。
    边界：不写文件、不打印、不上传、不发送远程日志。
    """

    event_ref: EventRef | None = None
    content_ref: ContentRef | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    metadata_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class LogSubmitResponse:
    """日志提交响应。

    作用：承载日志提交后的审计引用或事件引用。
    边界：不保证日志已持久化，不生成日志索引。
    """

    audit_ref: AuditRef | None = None
    event_ref: EventRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ClockPort(ABC):
    """时间端口。

    中文名称：时间查询端口。
    端口职责：定义查询时间事实或逻辑时间事实的 L1 协议。
    输入输出边界：输入 ClockQueryRequest 与 TraceContext，输出 PortResult 包装的 ClockQueryResponse。
    所属 L1 层：基础设施端口协议。
    不承担的实现职责：不读取真实系统时间，不同步时钟，不调度任务。
    """

    @abstractmethod
    def query_time(self, request: ClockQueryRequest, trace: TraceContext) -> PortResult[ClockQueryResponse]:
        """声明时间查询协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_infrastructure_boundary(self, trace: TraceContext) -> CoreResult[InfrastructurePortBoundary]:
        """声明基础设施边界说明协议。"""
        raise NotImplementedError


class IdGeneratorPort(ABC):
    """标识生成端口。

    中文名称：标识生成端口。
    端口职责：定义生成 L0 RefId 的请求和响应协议。
    输入输出边界：输入 IdGenerationRequest 与 TraceContext，输出 PortResult 包装的 IdGenerationResponse。
    所属 L1 层：基础设施端口协议。
    不承担的实现职责：不实现算法，不访问注册表，不保证外部唯一性。
    """

    @abstractmethod
    def generate_id(self, request: IdGenerationRequest, trace: TraceContext) -> PortResult[IdGenerationResponse]:
        """声明标识生成协议。"""
        raise NotImplementedError


class SerializationPort(ABC):
    """序列化端口。

    中文名称：序列化与反序列化端口。
    端口职责：定义载荷引用与内容引用之间的协议转换边界。
    输入输出边界：输入序列化请求或反序列化请求，输出 PortResult 包装的响应对象。
    所属 L1 层：基础设施端口协议。
    不承担的实现职责：不实现真实序列化器，不构造后续层对象，不访问文件或网络。
    """

    @abstractmethod
    def serialize_payload(self, request: SerializationRequest, trace: TraceContext) -> PortResult[SerializationResponse]:
        """声明序列化协议。"""
        raise NotImplementedError

    @abstractmethod
    def deserialize_content(self, request: DeserializationRequest, trace: TraceContext) -> PortResult[DeserializationResponse]:
        """声明反序列化协议。"""
        raise NotImplementedError


class HashPort(ABC):
    """摘要端口。

    中文名称：摘要事实端口。
    端口职责：定义对内容、载荷或资源形成摘要事实的协议。
    输入输出边界：输入 HashRequest 与 TraceContext，输出 PortResult 包装的 HashResponse。
    所属 L1 层：基础设施端口协议。
    不承担的实现职责：不读取真实内容，不执行摘要计算，不声明安全等级。
    """

    @abstractmethod
    def declare_hash(self, request: HashRequest, trace: TraceContext) -> PortResult[HashResponse]:
        """声明摘要事实协议。"""
        raise NotImplementedError


class LoggerPort(ABC):
    """日志端口。

    中文名称：日志提交端口。
    端口职责：定义日志事实提交的协议边界。
    输入输出边界：输入 LogSubmitRequest 与 TraceContext，输出 PortResult 包装的 LogSubmitResponse。
    所属 L1 层：基础设施端口协议。
    不承担的实现职责：不写日志、不打印、不发送远程日志、不生成日志存储。
    """

    @abstractmethod
    def submit_log(self, request: LogSubmitRequest, trace: TraceContext) -> PortResult[LogSubmitResponse]:
        """声明日志提交协议。"""
        raise NotImplementedError
