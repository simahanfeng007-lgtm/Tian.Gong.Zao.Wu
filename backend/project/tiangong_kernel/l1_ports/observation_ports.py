"""L1 观察、信号与遥测端口协议。

本模块在 L1 中的职责：定义观察提交、观察读取、信号传递与遥测提交端口协议。
本模块定义：ObservationSubmitPort、ObservationReadPort、SignalPort、TelemetryPort。
本模块不实现：真实环境观察、传感器采集、消息队列、遥测上报、状态推理或外部连接。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实环境、模型或工具。
本模块与 L2-L6 的关系：L2 可记录状态来源，L3 可提交运行观察，L4 可实现外部适配，L5 可记录插件健康，L6 可提交记忆、学习、检索与自愈观察事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.metric import MetricRef
from tiangong_kernel.l0_primitives.observation import (
    ObservationKind,
    ObservationPayloadRef,
    ObservationQuality,
    ObservationRef,
    ObservationSource,
    ObservationWindow,
)
from tiangong_kernel.l0_primitives.retrieval import QueryRef, QueryScopeRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalConfidence, SignalKind, SignalPolarity, SignalRef, SignalStrength, SignalWindow
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ObservationPortBoundary:
    """观察端口边界对象。

    作用：表达观察、信号与遥测端口的允许范围和禁止实现范围。
    边界：只描述协议，不采集环境，不触发真实动作。
    """

    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ObservationSubmitRequest:
    """观察提交请求。

    作用：声明一个观察事实需要提交到观察边界。
    边界：不采集真实环境，不解释观察含义，不修改状态。
    """

    observation_ref: ObservationRef
    kind: ObservationKind = ObservationKind.UNKNOWN
    quality: ObservationQuality = ObservationQuality.UNKNOWN
    source: ObservationSource | None = None
    window: ObservationWindow | None = None
    payload_ref: ObservationPayloadRef | PayloadRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ObservationSubmitResponse:
    """观察提交响应。

    作用：承载已提交或已声明的观察引用。
    边界：不代表观察已持久化，不代表已进入推理流程。
    """

    observation_ref: ObservationRef
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ObservationReadRequest:
    """观察读取请求。

    作用：声明按 ObservationRef 读取观察事实的协议需求。
    边界：不读取真实存储，不扫描环境，不生成观察。
    """

    observation_ref: ObservationRef
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ObservationReadResponse:
    """观察读取响应。

    作用：承载观察引用、载荷引用、来源与质量事实。
    边界：不返回真实环境数据，不进行可信度推理。
    """

    observation_ref: ObservationRef
    kind: ObservationKind = ObservationKind.UNKNOWN
    quality: ObservationQuality = ObservationQuality.UNKNOWN
    source: ObservationSource | None = None
    window: ObservationWindow | None = None
    payload_ref: ObservationPayloadRef | PayloadRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SignalSendRequest:
    """信号发送请求。

    作用：声明一个信号事实需要被提交给信号边界。
    边界：不触发真实行为，不驱动状态机，不执行消息队列。
    """

    signal_ref: SignalRef
    kind: SignalKind = SignalKind.UNKNOWN
    polarity: SignalPolarity = SignalPolarity.UNKNOWN
    strength: SignalStrength | None = None
    confidence: SignalConfidence | None = None
    window: SignalWindow | None = None
    source_observation_ref: ObservationRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SignalSendResponse:
    """信号发送响应。

    作用：承载被声明或接收的信号引用。
    边界：不代表信号已被消费，不触发任何动作。
    """

    signal_ref: SignalRef
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SignalReceiveRequest:
    """信号接收请求。

    作用：声明按信号引用或查询范围接收信号事实。
    边界：不创建订阅，不阻塞等待，不启动后台任务。
    """

    signal_ref: SignalRef | None = None
    query_ref: QueryRef | None = None
    query_scope_ref: QueryScopeRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SignalReceiveResponse:
    """信号接收响应。

    作用：承载可见的信号引用集合。
    边界：不代表消息队列已消费，不提供实时推送。
    """

    signal_refs: tuple[SignalRef, ...] = field(default_factory=tuple)
    query_ref: QueryRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TelemetrySubmitRequest:
    """遥测提交请求。

    作用：声明遥测事实由观察、信号、指标或载荷引用组成。
    边界：不采样，不上报远程服务，不连接外部系统。
    """

    observation_ref: ObservationRef | None = None
    signal_ref: SignalRef | None = None
    metric_ref: MetricRef | None = None
    payload_ref: PayloadRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class TelemetrySubmitResponse:
    """遥测提交响应。

    作用：承载遥测事实被声明后的观察、指标或审计引用。
    边界：不代表已完成远程上报，不生成遥测管道。
    """

    observation_ref: ObservationRef | None = None
    metric_ref: MetricRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ObservationSubmitPort(ABC):
    """观察提交端口。

    中文名称：观察提交端口。
    端口职责：定义观察事实提交的 L1 协议。
    输入输出边界：输入 ObservationSubmitRequest 与 TraceContext，输出 PortResult 包装的 ObservationSubmitResponse。
    所属 L1 层：观察端口协议。
    不承担的实现职责：不采集环境，不修改状态，不触发推理。
    """

    @abstractmethod
    def submit_observation(self, request: ObservationSubmitRequest, trace: TraceContext) -> PortResult[ObservationSubmitResponse]:
        """声明观察提交协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_observation_boundary(self, trace: TraceContext) -> CoreResult[ObservationPortBoundary]:
        """声明观察边界说明协议。"""
        raise NotImplementedError


class ObservationReadPort(ABC):
    """观察读取端口。

    中文名称：观察读取端口。
    端口职责：定义按 ObservationRef 读取观察事实的协议。
    输入输出边界：输入 ObservationReadRequest 与 TraceContext，输出 PortResult 包装的 ObservationReadResponse。
    所属 L1 层：观察端口协议。
    不承担的实现职责：不读取真实存储，不扫描环境，不生成观察。
    """

    @abstractmethod
    def read_observation(self, request: ObservationReadRequest, trace: TraceContext) -> PortResult[ObservationReadResponse]:
        """声明观察读取协议。"""
        raise NotImplementedError


class SignalPort(ABC):
    """信号端口。

    中文名称：信号发送与接收端口。
    端口职责：定义信号事实发送与接收的协议边界。
    输入输出边界：输入 SignalSendRequest 或 SignalReceiveRequest，输出 PortResult 包装的信号响应。
    所属 L1 层：观察端口协议。
    不承担的实现职责：不触发真实行为，不创建消息队列，不启动监听。
    """

    @abstractmethod
    def send_signal(self, request: SignalSendRequest, trace: TraceContext) -> PortResult[SignalSendResponse]:
        """声明信号发送协议。"""
        raise NotImplementedError

    @abstractmethod
    def receive_signal(self, request: SignalReceiveRequest, trace: TraceContext) -> PortResult[SignalReceiveResponse]:
        """声明信号接收协议。"""
        raise NotImplementedError


class TelemetryPort(ABC):
    """遥测端口。

    中文名称：遥测提交端口。
    端口职责：定义遥测事实提交的协议边界。
    输入输出边界：输入 TelemetrySubmitRequest 与 TraceContext，输出 PortResult 包装的 TelemetrySubmitResponse。
    所属 L1 层：观察端口协议。
    不承担的实现职责：不采样，不远程上报，不连接外部遥测系统。
    """

    @abstractmethod
    def submit_telemetry(self, request: TelemetrySubmitRequest, trace: TraceContext) -> PortResult[TelemetrySubmitResponse]:
        """声明遥测提交协议。"""
        raise NotImplementedError
