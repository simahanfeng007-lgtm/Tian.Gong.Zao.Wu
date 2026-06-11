"""L1 事件端口协议。

本模块在 L1 中的职责：定义事件追加、读取、流式声明与查询端口协议。
本模块定义：EventAppendPort、EventReadPort、EventStreamPort、EventQueryPort。
本模块不实现：事件存储、事件索引、事件分发、消息队列、后台监听或外部连接。
本模块禁止事项：不得访问文件、数据库、网络、线程、真实运行循环、模型或工具。
本模块与 L2-L6 的关系：L2 可引用事件来源，L3 可提交运行事件，L4 可实现适配，L5 可记录插件生命周期，L6 可提交子系统事件事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import PayloadRef
from tiangong_kernel.l0_primitives.event import CoreEvent, EventRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.retrieval import QueryRef, QueryScopeRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class EventPortBoundary:
    """事件端口边界对象。

    作用：表达事件端口可接受的事件范围、查询范围与禁止实现范围。
    边界：只描述协议，不创建事件存储，不执行分发。
    """

    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventAppendRequest:
    """事件追加请求。

    作用：声明需要追加的 L0 CoreEvent 事实。
    边界：不保存事件，不校验事件流完整性，不触发订阅者。
    """

    event: CoreEvent
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventAppendResponse:
    """事件追加响应。

    作用：承载被接受或声明的事件引用。
    边界：不代表事件已持久化，不代表已广播。
    """

    event_ref: EventRef
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventReadRequest:
    """事件读取请求。

    作用：声明读取某个事件事实的协议需求。
    边界：不访问真实存储，不回放事件，不启动事件订阅。
    """

    event_ref: EventRef
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventReadResponse:
    """事件读取响应。

    作用：承载读取到的事件事实或事件引用。
    边界：不保证来自数据库，不代表已完成审计。
    """

    event_ref: EventRef
    event: CoreEvent | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventStreamRequest:
    """事件流声明请求。

    作用：声明事件流读取或订阅的协议边界。
    边界：不启动后台任务，不建立网络连接，不创建消息队列。
    """

    scope_ref: ScopeRef | None = None
    query_scope_ref: QueryScopeRef | None = None
    start_event_ref: EventRef | None = None
    payload_ref: PayloadRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventStreamResponse:
    """事件流声明响应。

    作用：承载事件流可见的事件引用集合。
    边界：不代表实时流已经打开，不承诺推送能力。
    """

    event_refs: tuple[EventRef, ...] = field(default_factory=tuple)
    query_scope_ref: QueryScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventQueryRequest:
    """事件查询请求。

    作用：声明按查询引用和查询信封检索事件事实。
    边界：不实现索引，不执行聚合，不访问数据库。
    """

    query_ref: QueryRef
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    query_scope_ref: QueryScopeRef | None = None
    criteria_payload_ref: PayloadRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class EventQueryResponse:
    """事件查询响应。

    作用：承载查询得到的事件引用集合。
    边界：不排序、不打分、不生成查询索引。
    """

    event_refs: tuple[EventRef, ...] = field(default_factory=tuple)
    query_ref: QueryRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class EventAppendPort(ABC):
    """事件追加端口。

    中文名称：事件追加端口。
    端口职责：定义 CoreEvent 追加到事件边界的协议。
    输入输出边界：输入 EventAppendRequest 与 TraceContext，输出 PortResult 包装的 EventAppendResponse。
    所属 L1 层：事件端口协议。
    不承担的实现职责：不存储事件，不广播事件，不触发真实行为。
    """

    @abstractmethod
    def append_event(self, request: EventAppendRequest, trace: TraceContext) -> PortResult[EventAppendResponse]:
        """声明事件追加协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_event_boundary(self, trace: TraceContext) -> CoreResult[EventPortBoundary]:
        """声明事件边界说明协议。"""
        raise NotImplementedError


class EventReadPort(ABC):
    """事件读取端口。

    中文名称：事件读取端口。
    端口职责：定义按 EventRef 读取事件事实的协议。
    输入输出边界：输入 EventReadRequest 与 TraceContext，输出 PortResult 包装的 EventReadResponse。
    所属 L1 层：事件端口协议。
    不承担的实现职责：不读取文件、数据库或消息队列，不回放事件。
    """

    @abstractmethod
    def read_event(self, request: EventReadRequest, trace: TraceContext) -> PortResult[EventReadResponse]:
        """声明事件读取协议。"""
        raise NotImplementedError


class EventStreamPort(ABC):
    """事件流端口。

    中文名称：事件流声明端口。
    端口职责：定义事件流可见范围与返回引用的协议。
    输入输出边界：输入 EventStreamRequest 与 TraceContext，输出 PortResult 包装的 EventStreamResponse。
    所属 L1 层：事件端口协议。
    不承担的实现职责：不启动后台任务，不连接网络，不推送事件。
    """

    @abstractmethod
    def declare_event_stream(self, request: EventStreamRequest, trace: TraceContext) -> PortResult[EventStreamResponse]:
        """声明事件流协议。"""
        raise NotImplementedError


class EventQueryPort(ABC):
    """事件查询端口。

    中文名称：事件查询端口。
    端口职责：定义按 QueryRef 和 QueryEnvelope 查询事件引用的协议。
    输入输出边界：输入 EventQueryRequest 与 TraceContext，输出 PortResult 包装的 EventQueryResponse。
    所属 L1 层：事件端口协议。
    不承担的实现职责：不实现查询引擎，不聚合指标，不访问真实索引。
    """

    @abstractmethod
    def query_events(self, request: EventQueryRequest, trace: TraceContext) -> PortResult[EventQueryResponse]:
        """声明事件查询协议。"""
        raise NotImplementedError
