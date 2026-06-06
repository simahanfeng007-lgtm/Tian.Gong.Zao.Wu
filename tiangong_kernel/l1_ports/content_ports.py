"""L1 内容端口协议。

本模块在 L1 中的职责：定义内容存放、内容读取、写入意图、载荷、产物与证据端口协议。
本模块定义：ContentStorePort、ContentReadPort、ContentWriteIntentPort、PayloadPort、ArtifactPort、EvidencePort。
本模块不实现：真实内容存储、真实内容读取、真实文件写入、真实产物生成、真实证据复制或上传。
本模块禁止事项：不得访问文件、网络、数据库、外部通道、真实环境、模型或工具。
本模块与 L2-L6 的关系：L2 可引用内容事实，L3 可组织内容流与产物边界，L4 可实现外部适配，L5 可隔离插件内容边界，L6 可提交子系统内容引用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.artifact import ArtifactRef, ArtifactVersionRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentEncoding, ContentRef, MediaTypeRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef, EvidenceSourceRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ContentPortBoundary:
    """内容端口边界对象。

    作用：表达内容、载荷、产物与证据引用的协议边界。
    边界：只说明可引用范围，不存储内容，不生成产物，不绑定真实资源。
    """

    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    namespace_ref: NamespaceRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContentStoreRequest:
    """内容存放请求。

    作用：声明某个内容引用、载荷引用或产物引用需要进入内容边界。
    边界：不写文件，不写数据库，不保存真实字节。
    """

    content_ref: ContentRef
    payload_ref: PayloadRef | None = None
    artifact_ref: ArtifactRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    media_type_ref: MediaTypeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContentStoreResponse:
    """内容存放响应。

    作用：承载被接受的内容引用、载荷引用或审计引用。
    边界：不代表内容已持久化，不代表外部系统可读取。
    """

    content_ref: ContentRef
    payload_ref: PayloadRef | None = None
    artifact_ref: ArtifactRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContentReadRequest:
    """内容读取请求。

    作用：声明按 ContentRef 或 PayloadRef 读取内容事实的协议需求。
    边界：不读取真实文件，不访问真实网络，不访问真实数据库。
    """

    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContentReadResponse:
    """内容读取响应。

    作用：承载可见的内容引用、载荷引用、媒体类型或证据引用。
    边界：不返回裸字节，不保证来自真实存储。
    """

    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    media_type_ref: MediaTypeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContentWriteIntentRequest:
    """内容写入意图请求。

    作用：声明后续可能写入的内容、载荷、资源和产物意图。
    边界：只表达请求结构，不落盘，不覆盖文件，不占用真实资源。
    """

    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    resource_ref: ResourceRef | None = None
    artifact_ref: ArtifactRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContentWriteIntentResponse:
    """内容写入意图响应。

    作用：承载被接受的写入意图引用集合。
    边界：不代表已经写入，不代表允许覆盖，不替权限或策略层裁决。
    """

    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    resource_ref: ResourceRef | None = None
    artifact_ref: ArtifactRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PayloadDeclareRequest:
    """载荷声明请求。

    作用：声明 PayloadRef 与内容编码、媒体类型或结构版本之间的关系。
    边界：不实现真实编码器，不执行解码，不保存载荷内容。
    """

    payload_ref: PayloadRef
    content_ref: ContentRef | None = None
    encoding: ContentEncoding | None = None
    media_type_ref: MediaTypeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class PayloadDeclareResponse:
    """载荷声明响应。

    作用：承载被声明的 PayloadRef、ContentRef 与结构版本引用。
    边界：不返回解码后的对象，不生成真实内容。
    """

    payload_ref: PayloadRef
    content_ref: ContentRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ArtifactRegisterRequest:
    """产物登记请求。

    作用：声明产物引用、内容引用与版本引用之间的协议关系。
    边界：不生成真实产物，不导出文件，不上传外部系统。
    """

    artifact_ref: ArtifactRef
    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    artifact_version_ref: ArtifactVersionRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ArtifactRegisterResponse:
    """产物登记响应。

    作用：承载登记后的产物引用、内容引用与审计引用。
    边界：不代表产物已生成，不提供下载地址，不暴露真实路径。
    """

    artifact_ref: ArtifactRef
    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvidenceBindRequest:
    """内容证据绑定请求。

    作用：声明证据引用与内容、载荷、产物或资源引用之间的绑定关系。
    边界：不复制证据，不读取证据，不上传证据，不执行取证。
    """

    evidence_ref: EvidenceRef
    content_ref: ContentRef | None = None
    payload_ref: PayloadRef | None = None
    artifact_ref: ArtifactRef | None = None
    resource_ref: ResourceRef | None = None
    evidence_source_ref: EvidenceSourceRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EvidenceBindResponse:
    """内容证据绑定响应。

    作用：承载证据绑定后的证据引用与相关内容引用。
    边界：不代表证据已存储，不计算完整性链，不执行验签。
    """

    evidence_ref: EvidenceRef
    related_refs: tuple[ContentRef | PayloadRef | ArtifactRef | ResourceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


class ContentStorePort(ABC):
    """内容存放端口。

    中文名称：内容存放端口。
    端口职责：定义内容引用进入内容边界的 L1 协议。
    输入输出边界：输入 ContentStoreRequest 与 TraceContext，输出 PortResult 包装的 ContentStoreResponse。
    所属 L1 层：内容端口协议。
    不承担的实现职责：不存储真实内容，不写文件，不连接数据库。
    """

    @abstractmethod
    def store_content(self, request: ContentStoreRequest, trace: TraceContext) -> PortResult[ContentStoreResponse]:
        """声明内容存放协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_content_boundary(self, trace: TraceContext) -> CoreResult[ContentPortBoundary]:
        """声明内容边界说明协议。"""
        raise NotImplementedError


class ContentReadPort(ABC):
    """内容读取端口。

    中文名称：内容读取端口。
    端口职责：定义按内容引用读取内容事实的 L1 协议。
    输入输出边界：输入 ContentReadRequest 与 TraceContext，输出 PortResult 包装的 ContentReadResponse。
    所属 L1 层：内容端口协议。
    不承担的实现职责：不读取真实文件、网络或数据库，不返回裸字节。
    """

    @abstractmethod
    def read_content(self, request: ContentReadRequest, trace: TraceContext) -> PortResult[ContentReadResponse]:
        """声明内容读取协议。"""
        raise NotImplementedError


class ContentWriteIntentPort(ABC):
    """内容写入意图端口。

    中文名称：内容写入意图端口。
    端口职责：定义写入意图的结构化表达协议。
    输入输出边界：输入 ContentWriteIntentRequest 与 TraceContext，输出 PortResult 包装的 ContentWriteIntentResponse。
    所属 L1 层：内容端口协议。
    不承担的实现职责：不落盘，不覆盖文件，不执行真实写入。
    """

    @abstractmethod
    def declare_write_intent(
        self, request: ContentWriteIntentRequest, trace: TraceContext
    ) -> PortResult[ContentWriteIntentResponse]:
        """声明内容写入意图协议。"""
        raise NotImplementedError


class PayloadPort(ABC):
    """载荷端口。

    中文名称：载荷边界端口。
    端口职责：定义载荷引用、编码、解码边界的声明协议。
    输入输出边界：输入 PayloadDeclareRequest 与 TraceContext，输出 PortResult 包装的 PayloadDeclareResponse。
    所属 L1 层：内容端口协议。
    不承担的实现职责：不实现编码器或解码器，不构造真实对象。
    """

    @abstractmethod
    def declare_payload(self, request: PayloadDeclareRequest, trace: TraceContext) -> PortResult[PayloadDeclareResponse]:
        """声明载荷边界协议。"""
        raise NotImplementedError


class ArtifactPort(ABC):
    """产物端口。

    中文名称：产物登记端口。
    端口职责：定义产物引用、产物登记与产物边界的 L1 协议。
    输入输出边界：输入 ArtifactRegisterRequest 与 TraceContext，输出 PortResult 包装的 ArtifactRegisterResponse。
    所属 L1 层：内容端口协议。
    不承担的实现职责：不生成产物，不导出文件，不上传外部系统。
    """

    @abstractmethod
    def register_artifact(
        self, request: ArtifactRegisterRequest, trace: TraceContext
    ) -> PortResult[ArtifactRegisterResponse]:
        """声明产物登记协议。"""
        raise NotImplementedError


class EvidencePort(ABC):
    """证据端口。

    中文名称：内容证据绑定端口。
    端口职责：定义证据引用与内容、载荷、产物、资源引用的绑定协议。
    输入输出边界：输入 EvidenceBindRequest 与 TraceContext，输出 PortResult 包装的 EvidenceBindResponse。
    所属 L1 层：内容端口协议。
    不承担的实现职责：不复制证据，不上传证据，不读取证据材料。
    """

    @abstractmethod
    def bind_evidence(self, request: EvidenceBindRequest, trace: TraceContext) -> PortResult[EvidenceBindResponse]:
        """声明内容证据绑定协议。"""
        raise NotImplementedError
