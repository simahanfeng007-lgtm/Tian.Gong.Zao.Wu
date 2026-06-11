"""L1 审计端口协议。

本模块在 L1 中的职责：定义审计追加、审计读取与证据绑定端口协议。
本模块定义：AuditAppendPort、AuditReadPort、EvidenceAttachPort。
本模块不实现：审计落盘、审计库访问、证据复制、文件上传、合规判断或外部取证。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实外部系统、模型或工具。
本模块与 L2-L6 的关系：L2 可引用状态来源审计，L3 可记录编排审计，L4 可实现外部适配，L5 可记录插件生命周期，L6 可提交子系统证据引用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditEventRef, AuditRef, AuditTrailRef, IntegrityChainRef, ResponsibilityRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef, EvidenceSourceRef
from tiangong_kernel.l0_primitives.event import EventRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class AuditPortBoundary:
    """审计端口边界对象。

    作用：表达审计追加、读取与证据绑定的协议边界。
    边界：只描述协议，不落地审计材料，不执行取证。
    """

    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class AuditAppendRequest:
    """审计追加请求。

    作用：声明一个审计事实、审计事件或审计轨迹需要追加。
    边界：不写入审计库，不生成报告，不执行合规判断。
    """

    audit_ref: AuditRef
    audit_event_ref: AuditEventRef | None = None
    trail_ref: AuditTrailRef | None = None
    event_ref: EventRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    responsibility_ref: ResponsibilityRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class AuditAppendResponse:
    """审计追加响应。

    作用：承载被追加或被声明的审计引用。
    边界：不代表审计已落盘，不代表证据链完整。
    """

    audit_ref: AuditRef
    trail_ref: AuditTrailRef | None = None
    integrity_chain_ref: IntegrityChainRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class AuditReadRequest:
    """审计读取请求。

    作用：声明按审计引用、事件引用或轨迹引用读取审计事实。
    边界：不访问真实审计库，不扫描日志，不读取文件。
    """

    audit_ref: AuditRef | None = None
    audit_event_ref: AuditEventRef | None = None
    trail_ref: AuditTrailRef | None = None
    event_ref: EventRef | None = None
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class AuditReadResponse:
    """审计读取响应。

    作用：承载可见的审计引用、轨迹引用与证据引用。
    边界：不生成审计报告，不证明材料真实性。
    """

    audit_ref: AuditRef | None = None
    audit_event_refs: tuple[AuditEventRef, ...] = field(default_factory=tuple)
    trail_refs: tuple[AuditTrailRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvidenceAttachRequest:
    """证据绑定请求。

    作用：声明将证据引用绑定到审计、事件、内容、载荷或资源引用。
    边界：不复制文件，不上传文件，不读取文件，不做外部取证。
    """

    evidence_ref: EvidenceRef
    evidence_source_ref: EvidenceSourceRef | None = None
    audit_ref: AuditRef | None = None
    event_ref: EventRef | None = None
    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    resource_ref: ResourceRef | None = None
    responsibility_ref: ResponsibilityRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvidenceAttachResponse:
    """证据绑定响应。

    作用：承载证据绑定后的审计引用、证据引用与完整性链引用。
    边界：不代表证据已存储，不计算摘要链，不执行验签。
    """

    evidence_ref: EvidenceRef
    audit_ref: AuditRef | None = None
    integrity_chain_ref: IntegrityChainRef | None = None
    related_refs: tuple[ResourceRef | EventRef | ContentRef | PayloadRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class AuditAppendPort(ABC):
    """审计追加端口。

    中文名称：审计追加端口。
    端口职责：定义审计事实追加的 L1 协议。
    输入输出边界：输入 AuditAppendRequest 与 TraceContext，输出 PortResult 包装的 AuditAppendResponse。
    所属 L1 层：审计端口协议。
    不承担的实现职责：不落盘，不生成报告，不执行合规判断。
    """

    @abstractmethod
    def append_audit(self, request: AuditAppendRequest, trace: TraceContext) -> PortResult[AuditAppendResponse]:
        """声明审计追加协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_audit_boundary(self, trace: TraceContext) -> CoreResult[AuditPortBoundary]:
        """声明审计边界说明协议。"""
        raise NotImplementedError


class AuditReadPort(ABC):
    """审计读取端口。

    中文名称：审计读取端口。
    端口职责：定义按审计引用读取审计事实的协议。
    输入输出边界：输入 AuditReadRequest 与 TraceContext，输出 PortResult 包装的 AuditReadResponse。
    所属 L1 层：审计端口协议。
    不承担的实现职责：不访问真实审计库，不扫描日志，不生成审计报告。
    """

    @abstractmethod
    def read_audit(self, request: AuditReadRequest, trace: TraceContext) -> PortResult[AuditReadResponse]:
        """声明审计读取协议。"""
        raise NotImplementedError


class EvidenceAttachPort(ABC):
    """证据绑定端口。

    中文名称：证据引用绑定端口。
    端口职责：定义证据引用与审计、事件、内容、载荷或资源引用之间的绑定协议。
    输入输出边界：输入 EvidenceAttachRequest 与 TraceContext，输出 PortResult 包装的 EvidenceAttachResponse。
    所属 L1 层：审计端口协议。
    不承担的实现职责：不复制文件，不上传文件，不读取文件，不执行外部取证。
    """

    @abstractmethod
    def attach_evidence(self, request: EvidenceAttachRequest, trace: TraceContext) -> PortResult[EvidenceAttachResponse]:
        """声明证据引用绑定协议。"""
        raise NotImplementedError
