"""L1 通信端口协议。

本模块在 L1 中的职责：定义消息、通道、协议、交接与会话端口协议。
本模块定义：MessagePort、ChannelPort、ProtocolPort、HandoffPort、ConversationPort。
本模块不实现：真实聊天系统、真实通道连接、真实协议解析、真实消息发送、真实上下文拼接算法。
本模块禁止事项：不得访问网络、文件、数据库、外部通信系统、真实模型或真实工具。
本模块与 L2-L6 的关系：L2 可引用通信上下文，L3 可组织消息与交接边界，L4 可实现外部适配，L5 可隔离插件通信，L6 可传递子系统会话事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.communication import ChannelRef, ConversationRef, HandoffRef, ProtocolRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.message import CoreMessage, MessageRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class CommunicationPortBoundary:
    """通信端口边界对象。

    作用：表达消息、通道、协议、交接与会话的协议边界。
    边界：只描述通信边界，不建立真实连接，不发送消息。
    """

    boundary: PortBoundary
    channel_ref: ChannelRef | None = None
    protocol_ref: ProtocolRef | None = None
    conversation_ref: ConversationRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MessageSubmitRequest:
    """消息提交请求。

    作用：声明一个消息引用或核心消息需要进入通信边界。
    边界：不连接真实聊天系统，不发送外部消息，不持久化对话。
    """

    message_ref: MessageRef
    message: CoreMessage | None = None
    channel_ref: ChannelRef | None = None
    conversation_ref: ConversationRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    payload_ref: PayloadRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MessageSubmitResponse:
    """消息提交响应。

    作用：承载被接受的消息引用、通道引用与审计引用。
    边界：不代表消息已发送，不代表外部系统已接收。
    """

    message_ref: MessageRef
    channel_ref: ChannelRef | None = None
    conversation_ref: ConversationRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MessageReadRequest:
    """消息读取请求。

    作用：声明按消息引用、会话引用或查询信封读取消息事实。
    边界：不读取真实对话库，不拼接真实上下文，不访问外部通道。
    """

    message_ref: MessageRef | None = None
    conversation_ref: ConversationRef | None = None
    channel_ref: ChannelRef | None = None
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MessageReadResponse:
    """消息读取响应。

    作用：承载可见的消息引用、核心消息或内容引用。
    边界：不保证来自真实存储，不执行上下文裁剪或排序。
    """

    message_refs: tuple[MessageRef, ...] = field(default_factory=tuple)
    messages: tuple[CoreMessage, ...] = field(default_factory=tuple)
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ChannelOpenIntentRequest:
    """通道启用意图请求。

    作用：声明某个通道引用希望进入可用边界的意图。
    边界：不建立真实连接，不握手，不发送网络请求。
    """

    channel_ref: ChannelRef
    protocol_ref: ProtocolRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ChannelOpenIntentResponse:
    """通道启用意图响应。

    作用：承载通道意图被接受后的通道引用与协议引用。
    边界：不代表真实通道已连接，不承诺可发送消息。
    """

    channel_ref: ChannelRef
    protocol_ref: ProtocolRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ProtocolDeclareRequest:
    """协议声明请求。

    作用：声明通信协议引用、结构版本与通道边界之间的关系。
    边界：不实现协议解析器，不解析真实报文，不访问网络。
    """

    protocol_ref: ProtocolRef
    channel_ref: ChannelRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    payload_ref: PayloadRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ProtocolDeclareResponse:
    """协议声明响应。

    作用：承载被声明的协议引用、通道引用和版本引用。
    边界：不代表协议已加载，不执行解析或编码。
    """

    protocol_ref: ProtocolRef
    channel_ref: ChannelRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class HandoffSubmitRequest:
    """交接提交请求。

    作用：声明一次交接引用、内容引用或消息引用需要进入交接边界。
    边界：不发送真实交接消息，不写外部系统，不触发任务。
    """

    handoff_ref: HandoffRef
    message_ref: MessageRef | None = None
    content_ref: ContentRef | None = None
    conversation_ref: ConversationRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class HandoffSubmitResponse:
    """交接提交响应。

    作用：承载被接受的交接引用、消息引用与审计引用。
    边界：不代表外部接收方已收到，不代表任务已移交执行。
    """

    handoff_ref: HandoffRef
    message_ref: MessageRef | None = None
    conversation_ref: ConversationRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ConversationReferenceRequest:
    """会话引用请求。

    作用：声明会话引用、消息引用和查询信封之间的边界关系。
    边界：不实现对话存储，不执行真实上下文拼接算法。
    """

    conversation_ref: ConversationRef
    message_refs: tuple[MessageRef, ...] = field(default_factory=tuple)
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ConversationReferenceResponse:
    """会话引用响应。

    作用：承载会话引用、消息引用和内容引用集合。
    边界：不代表上下文已经拼接，不裁剪、不排序、不改写消息。
    """

    conversation_ref: ConversationRef
    message_refs: tuple[MessageRef, ...] = field(default_factory=tuple)
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class MessagePort(ABC):
    """消息端口。

    中文名称：消息端口。
    端口职责：定义消息提交、消息读取与消息引用协议。
    输入输出边界：输入消息请求与 TraceContext，输出 PortResult 包装的消息响应。
    所属 L1 层：通信端口协议。
    不承担的实现职责：不连接真实聊天系统，不发送外部消息，不持久化对话。
    """

    @abstractmethod
    def submit_message(self, request: MessageSubmitRequest, trace: TraceContext) -> PortResult[MessageSubmitResponse]:
        """声明消息提交协议。"""
        raise NotImplementedError

    @abstractmethod
    def read_message(self, request: MessageReadRequest, trace: TraceContext) -> PortResult[MessageReadResponse]:
        """声明消息读取协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_communication_boundary(self, trace: TraceContext) -> CoreResult[CommunicationPortBoundary]:
        """声明通信边界说明协议。"""
        raise NotImplementedError


class ChannelPort(ABC):
    """通道端口。

    中文名称：通道边界端口。
    端口职责：定义通道引用和通道启用意图的 L1 协议。
    输入输出边界：输入 ChannelOpenIntentRequest 与 TraceContext，输出 PortResult 包装的 ChannelOpenIntentResponse。
    所属 L1 层：通信端口协议。
    不承担的实现职责：不建立真实连接，不实现外部通道适配。
    """

    @abstractmethod
    def declare_channel_intent(
        self, request: ChannelOpenIntentRequest, trace: TraceContext
    ) -> PortResult[ChannelOpenIntentResponse]:
        """声明通道启用意图协议。"""
        raise NotImplementedError


class ProtocolPort(ABC):
    """协议端口。

    中文名称：协议声明端口。
    端口职责：定义通信协议引用和协议声明的 L1 边界。
    输入输出边界：输入 ProtocolDeclareRequest 与 TraceContext，输出 PortResult 包装的 ProtocolDeclareResponse。
    所属 L1 层：通信端口协议。
    不承担的实现职责：不解析报文，不实现协议栈，不发起网络请求。
    """

    @abstractmethod
    def declare_protocol(
        self, request: ProtocolDeclareRequest, trace: TraceContext
    ) -> PortResult[ProtocolDeclareResponse]:
        """声明协议边界协议。"""
        raise NotImplementedError


class HandoffPort(ABC):
    """交接端口。

    中文名称：交接端口。
    端口职责：定义交接引用、交接内容与交接边界的 L1 协议。
    输入输出边界：输入 HandoffSubmitRequest 与 TraceContext，输出 PortResult 包装的 HandoffSubmitResponse。
    所属 L1 层：通信端口协议。
    不承担的实现职责：不发送真实交接消息，不写外部系统，不触发任务。
    """

    @abstractmethod
    def submit_handoff(self, request: HandoffSubmitRequest, trace: TraceContext) -> PortResult[HandoffSubmitResponse]:
        """声明交接提交协议。"""
        raise NotImplementedError


class ConversationPort(ABC):
    """会话端口。

    中文名称：会话引用端口。
    端口职责：定义会话引用与会话边界的 L1 协议。
    输入输出边界：输入 ConversationReferenceRequest 与 TraceContext，输出 PortResult 包装的 ConversationReferenceResponse。
    所属 L1 层：通信端口协议。
    不承担的实现职责：不实现对话存储，不拼接真实上下文算法。
    """

    @abstractmethod
    def reference_conversation(
        self, request: ConversationReferenceRequest, trace: TraceContext
    ) -> PortResult[ConversationReferenceResponse]:
        """声明会话引用协议。"""
        raise NotImplementedError
