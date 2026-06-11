"""L1 记忆端口协议。

本模块在 L1 中的职责：定义记忆引用、记忆写入意图、读取意图、轨迹绑定、晋升提示、保留边界和遗忘意图协议。
本模块定义哪些端口：MemoryReferencePort、MemoryWriteIntentPort、MemoryReadIntentPort、MemoryTracePort、MemoryPromotionHintPort、MemoryRetentionBoundaryPort、ForgettingIntentPort。
本模块不实现哪些能力：不实现真实记忆库、不写入、不读取、不晋升、不遗忘、不做召回或相似度计算。
本模块禁止事项：不得访问文件、网络、数据库、模型、工具、插件或任何真实记忆系统。
本模块与 L2-L6 的关系：L2 可记录记忆状态，L3 可编排意图，L4 可实现外部适配，L5 可隔离插件记忆边界，L6 可由子系统提交候选。
本模块如何服务工程生命体：把经验、事件、观察和证据转成可引用的生命体记忆事实入口。
本模块如何保证学习 / 迭代 / 进化不绕过边界：所有记忆写入、晋升和遗忘都只是意图或提示，后续层必须再验证和裁决。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.context import ContextRef
from tiangong_kernel.l0_primitives.event import EventRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.forgetting import ForgettingRef, PruningRef, RevisionRef, SuppressionRef
from tiangong_kernel.l0_primitives.memory import MemoryRef, MemoryRetentionRef, MemoryTraceRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef

from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class MemoryReference:
    """记忆引用声明对象。

    作用：表达某条记忆、来源、上下文和证据的引用关系。
    边界：不保存记忆正文，不读取真实记忆，不建立索引。
    """

    memory_ref: MemoryRef
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    content_ref: ContentRef | None = None
    context_ref: ContextRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryWriteIntent:
    """记忆写入意图对象。

    作用：表达后续层可能需要写入的记忆候选及其来源。
    边界：不写入真实记忆，不晋升长期记忆，不修改已有记忆。
    """

    intent_ref: ResourceRef
    memory_ref: MemoryRef | None = None
    content_ref: ContentRef | None = None
    source_event_ref: EventRef | None = None
    source_observation_ref: ObservationRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryReadIntent:
    """记忆读取意图对象。

    作用：表达后续层可能需要读取或召回的记忆引用范围。
    边界：不读取真实存储，不执行召回算法，不计算相似度。
    """

    intent_ref: ResourceRef
    memory_ref: MemoryRef | None = None
    query: QueryEnvelope | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryTraceBinding:
    """记忆轨迹绑定对象。

    作用：表达记忆与事件、观察、信号、证据之间的引用轨迹。
    边界：不落盘，不生成真实索引，不折叠历史。
    """

    trace_ref: MemoryTraceRef
    memory_ref: MemoryRef | None = None
    event_refs: tuple[EventRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    signal_refs: tuple[SignalRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryTrace:
    """记忆轨迹对象。

    作用：表达某条记忆轨迹引用与证据、审计之间的关系。
    边界：不建立真实索引，不落盘，不折叠真实轨迹。
    """

    trace_ref: MemoryTraceRef
    memory_ref: MemoryRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[AuditRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


MemoryTraceLink = MemoryTraceBinding


@dataclass(frozen=True, slots=True)
class MemoryPromotionHint:
    """记忆晋升提示对象。

    作用：表达某条记忆可能需要被更高层复核或晋升的候选提示。
    边界：不执行晋升，不计算记忆评分，不改变记忆等级。
    """

    memory_ref: MemoryRef
    reason_ref: SignalRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryRetentionBoundary:
    """记忆保留边界对象。

    作用：表达记忆保留、抑制、剪枝、修订或忘却的边界引用。
    边界：不删除数据，不执行保留策略，不执行遗忘算法。
    """

    memory_ref: MemoryRef
    retention_ref: MemoryRetentionRef | None = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    suppression_ref: SuppressionRef | None = None
    pruning_ref: PruningRef | None = None
    revision_ref: RevisionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ForgettingIntent:
    """遗忘意图对象。

    作用：表达后续层可能需要遗忘、抑制或剪枝的候选意图。
    边界：不删除真实数据，不清空记忆，不执行物理瘦身。
    """

    intent_ref: ResourceRef
    memory_ref: MemoryRef | None = None
    forgetting_ref: ForgettingRef | None = None
    boundary: MemoryRetentionBoundary | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryReferenceRequest:
    """记忆引用请求。作用：提交记忆引用声明；边界：不读取真实记忆。"""

    reference: MemoryReference
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryReferenceResponse:
    """记忆引用响应。作用：返回记忆引用声明；边界：不代表记忆已写入。"""

    reference: MemoryReference
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryWriteIntentRequest:
    """记忆写入意图请求。作用：提交写入候选；边界：不写入。"""

    intent: MemoryWriteIntent
    command: CommandEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryWriteIntentResponse:
    """记忆写入意图响应。作用：返回写入候选和证据；边界：不修改长期记忆。"""

    intent: MemoryWriteIntent
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryReadIntentRequest:
    """记忆读取意图请求。作用：提交读取候选；边界：不执行召回。"""

    intent: MemoryReadIntent
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryReadIntentResponse:
    """记忆读取意图响应。作用：返回读取意图；边界：不返回真实记忆正文。"""

    intent: MemoryReadIntent
    memory_refs: tuple[MemoryRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryTraceRequest:
    """记忆轨迹请求。作用：提交记忆轨迹绑定；边界：不落盘。"""

    binding: MemoryTraceBinding
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryTraceResponse:
    """记忆轨迹响应。作用：返回轨迹绑定；边界：不生成索引。"""

    binding: MemoryTraceBinding
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryPromotionHintRequest:
    """记忆晋升提示请求。作用：提交晋升候选；边界：不执行晋升。"""

    hint: MemoryPromotionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryPromotionHintResponse:
    """记忆晋升提示响应。作用：返回晋升提示；边界：不代表晋升通过。"""

    hint: MemoryPromotionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryRetentionBoundaryRequest:
    """记忆保留边界请求。作用：提交保留边界声明；边界：不删除数据。"""

    boundary: MemoryRetentionBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MemoryRetentionBoundaryResponse:
    """记忆保留边界响应。作用：返回保留边界；边界：不执行遗忘策略。"""

    boundary: MemoryRetentionBoundary
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ForgettingIntentRequest:
    """遗忘意图请求。作用：提交遗忘候选；边界：不执行删除。"""

    intent: ForgettingIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ForgettingIntentResponse:
    """遗忘意图响应。作用：返回遗忘意图；边界：不清空记忆。"""

    intent: ForgettingIntent
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


class MemoryReferencePort(ABC):
    """记忆引用端口。

    中文名称：记忆引用端口。
    端口职责：定义记忆事实的引用声明协议。
    输入输出边界：输入 MemoryReferenceRequest 与 TraceContext，输出 PortResult 包装的 MemoryReferenceResponse。
    所属 L1 层：记忆、上下文、检索、自我学习、自我迭代、自我进化端口协议。
    不承担的实现职责：不保存记忆，不读取记忆，不建立记忆库。
    如何服务大模型执行力：让模型反馈和观察可以被后续层结构化引用。
    如何维持绝对边界：只暴露引用事实，不暴露真实内容和存储能力。
    与后续 L2-L6 的关系：后续层可实现状态记录、外部适配和子系统提交。
    """

    @abstractmethod
    def reference_memory(self, request: MemoryReferenceRequest, trace: TraceContext) -> PortResult[MemoryReferenceResponse]:
        """声明记忆引用协议。"""
        raise NotImplementedError


class MemoryWriteIntentPort(ABC):
    """记忆写入意图端口。

    中文名称：记忆写入意图端口。
    端口职责：定义写入记忆候选的提交协议。
    输入输出边界：输入 MemoryWriteIntentRequest 与 TraceContext，输出 PortResult 包装的 MemoryWriteIntentResponse。
    所属 L1 层：记忆协议入口。
    不承担的实现职责：不写入、不晋升、不修改长期记忆。
    如何服务大模型执行力：把有价值反馈转为后续可复核候选。
    如何维持绝对边界：写入只是意图，必须等待后续验证。
    与后续 L2-L6 的关系：L3 可编排，L4 可实现，L6 可提交候选。
    """

    @abstractmethod
    def submit_memory_write_intent(self, request: MemoryWriteIntentRequest, trace: TraceContext) -> PortResult[MemoryWriteIntentResponse]:
        """声明记忆写入意图协议。"""
        raise NotImplementedError


class MemoryReadIntentPort(ABC):
    """记忆读取意图端口。

    中文名称：记忆读取意图端口。
    端口职责：定义读取记忆的候选请求协议。
    输入输出边界：输入 MemoryReadIntentRequest 与 TraceContext，输出 PortResult 包装的 MemoryReadIntentResponse。
    所属 L1 层：记忆协议入口。
    不承担的实现职责：不读取、不召回、不排序真实记忆。
    如何服务大模型执行力：让后续编排层明确模型需要哪些记忆范围。
    如何维持绝对边界：只描述需求，不释放真实内容。
    与后续 L2-L6 的关系：后续层可绑定检索和上下文边界。
    """

    @abstractmethod
    def submit_memory_read_intent(self, request: MemoryReadIntentRequest, trace: TraceContext) -> PortResult[MemoryReadIntentResponse]:
        """声明记忆读取意图协议。"""
        raise NotImplementedError


class MemoryTracePort(ABC):
    """记忆轨迹端口。

    中文名称：记忆轨迹端口。
    端口职责：定义记忆与事件、观察、信号和证据的轨迹绑定协议。
    输入输出边界：输入 MemoryTraceRequest 与 TraceContext，输出 PortResult 包装的 MemoryTraceResponse。
    所属 L1 层：记忆协议入口。
    不承担的实现职责：不落盘、不索引、不折叠历史。
    如何服务大模型执行力：为模型后续反思提供可追溯引用链。
    如何维持绝对边界：仅记录引用关系，不接触真实内容。
    与后续 L2-L6 的关系：后续层可用该引用链做状态和审计关联。
    """

    @abstractmethod
    def bind_memory_trace(self, request: MemoryTraceRequest, trace: TraceContext) -> PortResult[MemoryTraceResponse]:
        """声明记忆轨迹绑定协议。"""
        raise NotImplementedError


class MemoryPromotionHintPort(ABC):
    """记忆晋升提示端口。

    中文名称：记忆晋升提示端口。
    端口职责：定义记忆可能需要晋升的候选提示协议。
    输入输出边界：输入 MemoryPromotionHintRequest 与 TraceContext，输出 PortResult 包装的 MemoryPromotionHintResponse。
    所属 L1 层：记忆协议入口。
    不承担的实现职责：不计算评分、不晋升、不改写记忆层级。
    如何服务大模型执行力：让模型经验沉淀可以形成稳定候选。
    如何维持绝对边界：晋升提示必须等待后续验证和边界处理。
    与后续 L2-L6 的关系：L2 可记录状态，L3 可调度复核。
    """

    @abstractmethod
    def submit_memory_promotion_hint(self, request: MemoryPromotionHintRequest, trace: TraceContext) -> PortResult[MemoryPromotionHintResponse]:
        """声明记忆晋升提示协议。"""
        raise NotImplementedError


class MemoryRetentionBoundaryPort(ABC):
    """记忆保留边界端口。

    中文名称：记忆保留边界端口。
    端口职责：定义记忆保留和忘却边界说明协议。
    输入输出边界：输入 MemoryRetentionBoundaryRequest 与 TraceContext，输出 PortResult 包装的 MemoryRetentionBoundaryResponse。
    所属 L1 层：记忆协议入口。
    不承担的实现职责：不执行删除、不执行遗忘算法、不清理数据。
    如何服务大模型执行力：给后续上下文和记忆使用提供可解释边界。
    如何维持绝对边界：边界声明不等于动作执行。
    与后续 L2-L6 的关系：后续层可实现策略和审计适配。
    """

    @abstractmethod
    def describe_memory_retention_boundary(self, request: MemoryRetentionBoundaryRequest, trace: TraceContext) -> PortResult[MemoryRetentionBoundaryResponse]:
        """声明记忆保留边界协议。"""
        raise NotImplementedError


class ForgettingIntentPort(ABC):
    """遗忘意图端口。

    中文名称：遗忘意图端口。
    端口职责：定义遗忘、抑制或剪枝的候选意图协议。
    输入输出边界：输入 ForgettingIntentRequest 与 TraceContext，输出 PortResult 包装的 ForgettingIntentResponse。
    所属 L1 层：记忆协议入口。
    不承担的实现职责：不删除真实数据、不清空记忆、不执行物理瘦身。
    如何服务大模型执行力：让模型可表达噪声或错误记忆处理需求。
    如何维持绝对边界：遗忘必须经后续验证和回退边界处理。
    与后续 L2-L6 的关系：后续层可实现复核、审计和治理。
    """

    @abstractmethod
    def submit_forgetting_intent(self, request: ForgettingIntentRequest, trace: TraceContext) -> PortResult[ForgettingIntentResponse]:
        """声明遗忘意图协议。"""
        raise NotImplementedError
