"""L1 指标端口协议。

本模块在 L1 中的职责：定义指标记录、读取与查询端口协议。
本模块定义：MetricRecordPort、MetricReadPort、MetricQueryPort。
本模块不实现：真实指标采样、指标数据库、聚合算法、远程上报或监控系统。
本模块禁止事项：不得访问文件、数据库、网络、后台任务、真实环境、模型或工具。
本模块与 L2-L6 的关系：L2 可引用指标事实表达状态来源，L3 可记录编排指标，L4 可实现外部适配，L5 可记录插件健康，L6 可提交子系统指标事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.metric import MetricKind, MetricPoint, MetricRef, MetricSeriesRef, MetricWindow
from tiangong_kernel.l0_primitives.retrieval import QueryRef, QueryScopeRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class MetricPortBoundary:
    """指标端口边界对象。

    作用：表达指标端口的记录、读取与查询边界。
    边界：只描述协议，不执行采样、聚合或上报。
    """

    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MetricRecordRequest:
    """指标记录请求。

    作用：声明一个 L0 MetricPoint 或 MetricRef 需要被记录。
    边界：不写入真实指标系统，不采样，不上报。
    """

    metric_ref: MetricRef
    metric_point: MetricPoint | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    payload_ref: PayloadRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MetricRecordResponse:
    """指标记录响应。

    作用：承载被记录或被声明的指标引用。
    边界：不代表指标已持久化，不代表已被聚合。
    """

    metric_ref: MetricRef
    series_ref: MetricSeriesRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MetricReadRequest:
    """指标读取请求。

    作用：声明按 MetricRef 或 MetricSeriesRef 读取指标事实。
    边界：不访问真实数据库，不读取监控系统。
    """

    metric_ref: MetricRef | None = None
    series_ref: MetricSeriesRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MetricReadResponse:
    """指标读取响应。

    作用：承载指标点、指标引用或指标序列引用。
    边界：不计算聚合值，不生成图表，不访问真实存储。
    """

    metric_ref: MetricRef | None = None
    series_ref: MetricSeriesRef | None = None
    metric_point: MetricPoint | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MetricQueryRequest:
    """指标查询请求。

    作用：声明按 QueryRef、指标类别与时间窗口查询指标引用。
    边界：不实现聚合算法，不访问指标数据库，不排序打分。
    """

    query_ref: QueryRef
    query: QueryEnvelope | None = None
    metric_kind: MetricKind = MetricKind.UNKNOWN
    window: MetricWindow | None = None
    scope_ref: ScopeRef | None = None
    query_scope_ref: QueryScopeRef | None = None
    criteria_payload_ref: PayloadRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MetricQueryResponse:
    """指标查询响应。

    作用：承载查询得到的指标引用或指标序列引用集合。
    边界：不执行聚合，不保证查询来源，不生成指标索引。
    """

    metric_refs: tuple[MetricRef, ...] = field(default_factory=tuple)
    series_refs: tuple[MetricSeriesRef, ...] = field(default_factory=tuple)
    query_ref: QueryRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class MetricRecordPort(ABC):
    """指标记录端口。

    中文名称：指标记录端口。
    端口职责：定义指标事实记录的 L1 协议。
    输入输出边界：输入 MetricRecordRequest 与 TraceContext，输出 PortResult 包装的 MetricRecordResponse。
    所属 L1 层：指标端口协议。
    不承担的实现职责：不采样、不写入指标系统、不远程上报。
    """

    @abstractmethod
    def record_metric(self, request: MetricRecordRequest, trace: TraceContext) -> PortResult[MetricRecordResponse]:
        """声明指标记录协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_metric_boundary(self, trace: TraceContext) -> CoreResult[MetricPortBoundary]:
        """声明指标边界说明协议。"""
        raise NotImplementedError


class MetricReadPort(ABC):
    """指标读取端口。

    中文名称：指标读取端口。
    端口职责：定义按指标引用读取指标事实的协议。
    输入输出边界：输入 MetricReadRequest 与 TraceContext，输出 PortResult 包装的 MetricReadResponse。
    所属 L1 层：指标端口协议。
    不承担的实现职责：不访问真实数据库，不计算指标，不生成报表。
    """

    @abstractmethod
    def read_metric(self, request: MetricReadRequest, trace: TraceContext) -> PortResult[MetricReadResponse]:
        """声明指标读取协议。"""
        raise NotImplementedError


class MetricQueryPort(ABC):
    """指标查询端口。

    中文名称：指标查询端口。
    端口职责：定义按 QueryRef 查询指标引用的协议。
    输入输出边界：输入 MetricQueryRequest 与 TraceContext，输出 PortResult 包装的 MetricQueryResponse。
    所属 L1 层：指标端口协议。
    不承担的实现职责：不实现聚合算法，不读取真实存储，不生成指标索引。
    """

    @abstractmethod
    def query_metrics(self, request: MetricQueryRequest, trace: TraceContext) -> PortResult[MetricQueryResponse]:
        """声明指标查询协议。"""
        raise NotImplementedError
