"""L1 上下文端口协议。

本模块在 L1 中的职责：定义上下文引用、窗口、组装意图、使用边界、压缩提示和跨轮延续协议。
本模块定义哪些端口：ContextReferencePort、ContextWindowPort、ContextAssemblyIntentPort、ContextBoundaryPort、ContextCompressionHintPort、ContextCarryoverPort。
本模块不实现哪些能力：不拼接真实提示词、不读取记忆或文件、不压缩上下文、不计算真实 token、不持久化会话。
本模块禁止事项：不得访问文件、网络、数据库、模型、工具、插件或真实上下文存储。
本模块与 L2-L6 的关系：L2 可记录上下文状态，L3 可编排上下文候选，L4 可实现适配，L5 可隔离插件，L6 可提交子系统上下文引用。
本模块如何服务工程生命体：让生命体在不同任务、Skill 和观察之间保留清晰的上下文边界。
本模块如何保证学习 / 迭代 / 进化不绕过边界：上下文只提供引用与边界，不把未经验证的候选直接送入模型或系统修改链。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.context import ContextBoundary as L0ContextBoundary
from tiangong_kernel.l0_primitives.context import ContextRef, ContextWindow
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.memory import MemoryRef
from tiangong_kernel.l0_primitives.message import MessageRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef

from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .model_ports import ModelContextView
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ContextReference:
    """上下文引用声明对象。

    作用：表达上下文、主体、作用域、消息、内容和证据之间的引用关系。
    边界：不读取真实上下文，不保存消息列表，不拼接模型输入。
    """

    context_ref: ContextRef
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    message_refs: tuple[MessageRef, ...] = field(default_factory=tuple)
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextWindowDeclaration:
    """上下文窗口声明对象。

    作用：表达上下文窗口、预算引用、Skill 引用和可见边界。
    边界：不计算真实 token，不裁剪上下文，不压缩内容。
    """

    context_ref: ContextRef
    window: ContextWindow | None = None
    budget_ref: ResourceRef | None = None
    skill_ref: SkillRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextAssemblyIntent:
    """上下文组装意图对象。

    作用：表达后续层可能需要将内容、记忆、观察和消息组织为上下文候选。
    边界：不拼接真实提示词，不调用模型，不读取文件或记忆。
    """

    intent_ref: ResourceRef
    context_ref: ContextRef | None = None
    memory_refs: tuple[MemoryRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    payload_refs: tuple[PayloadRef, ...] = field(default_factory=tuple)
    model_context_view: ModelContextView | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextUseBoundary:
    """上下文使用边界对象。

    作用：表达哪些上下文引用可见、可引用、可使用或必须隔离。
    边界：不执行真实裁决，不过滤内容，不释放敏感信息。
    """

    context_ref: ContextRef
    l0_boundary: L0ContextBoundary | None = None
    port_boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextUsageBoundary:
    """上下文使用边界兼容对象。

    作用：表达第七阶段测试与交接中使用的上下文边界字段。
    边界：不执行真实裁决，不过滤内容，不释放敏感信息。
    """

    context_ref: ContextRef
    boundary: L0ContextBoundary | None = None
    port_boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"



ContextBoundaryDeclaration = ContextUsageBoundary


@dataclass(frozen=True, slots=True)
class ContextWindowBoundary:
    """上下文窗口边界对象。

    作用：表达上下文窗口对应的 L0 边界和端口边界引用。
    边界：不计算真实 token，不裁剪上下文，不组装模型输入。
    """

    context_ref: ContextRef | None = None
    boundary: L0ContextBoundary | None = None
    port_boundary: PortBoundary | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextBoundaryDeclaration:
    """上下文边界声明对象。

    作用：表达上下文使用边界、策略引用和越界事实。
    边界：不执行真实裁决，不过滤真实内容。
    """

    context_ref: ContextRef | None = None
    boundary: L0ContextBoundary | None = None
    port_boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextCompressionHint:
    """上下文压缩提示对象。

    作用：表达后续层可能需要压缩、摘要或降噪的上下文候选提示。
    边界：不实现压缩算法，不总结真实内容，不计算 token。
    """

    hint_ref: ResourceRef
    context_ref: ContextRef | None = None
    reason_ref: SignalRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextCarryover:
    """上下文延续对象。

    作用：表达跨轮、跨任务、跨 Skill 的上下文延续引用。
    边界：不持久化真实会话，不拼接历史，不读取长期记忆。
    """

    source_context_ref: ContextRef
    target_context_ref: ContextRef | None = None
    skill_ref: SkillRef | None = None
    audit_ref: AuditRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextReferenceRequest:
    """上下文引用请求。作用：提交上下文引用；边界：不读取上下文。"""

    reference: ContextReference
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextReferenceResponse:
    """上下文引用响应。作用：返回上下文引用；边界：不代表上下文已装配。"""

    reference: ContextReference
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextWindowRequest:
    """上下文窗口请求。作用：提交窗口声明；边界：不计算真实 token。"""

    declaration: ContextWindowDeclaration
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextWindowResponse:
    """上下文窗口响应。作用：返回窗口声明；边界：不裁剪内容。"""

    declaration: ContextWindowDeclaration
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextAssemblyIntentRequest:
    """上下文组装意图请求。作用：提交组装候选；边界：不拼接提示词。"""

    intent: ContextAssemblyIntent
    command: CommandEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextAssemblyIntentResponse:
    """上下文组装意图响应。作用：返回组装意图；边界：不生成模型输入。"""

    intent: ContextAssemblyIntent
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextBoundaryRequest:
    """上下文边界请求。作用：提交上下文使用边界；边界：不执行真实过滤。"""

    boundary: ContextUseBoundary
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextBoundaryResponse:
    """上下文边界响应。作用：返回上下文边界；边界：不释放内容。"""

    boundary: ContextUseBoundary
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextCompressionHintRequest:
    """上下文压缩提示请求。作用：提交压缩提示；边界：不执行压缩。"""

    hint: ContextCompressionHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextCompressionHintResponse:
    """上下文压缩提示响应。作用：返回压缩提示；边界：不生成摘要。"""

    hint: ContextCompressionHint
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextCarryoverRequest:
    """上下文延续请求。作用：提交跨轮延续引用；边界：不持久化会话。"""

    carryover: ContextCarryover
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ContextCarryoverResponse:
    """上下文延续响应。作用：返回延续引用；边界：不拼接历史。"""

    carryover: ContextCarryover
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


class ContextReferencePort(ABC):
    """上下文引用端口。

    中文名称：上下文引用端口。
    端口职责：定义上下文引用声明协议。
    输入输出边界：输入 ContextReferenceRequest 与 TraceContext，输出 PortResult 包装的 ContextReferenceResponse。
    所属 L1 层：上下文协议入口。
    不承担的实现职责：不读取上下文，不保存消息列表，不拼接模型输入。
    如何服务大模型执行力：明确模型可以引用的上下文事实边界。
    如何维持绝对边界：只传递引用，不暴露真实内容。
    与后续 L2-L6 的关系：后续层可实现状态记录和适配。
    """

    @abstractmethod
    def reference_context(self, request: ContextReferenceRequest, trace: TraceContext) -> PortResult[ContextReferenceResponse]:
        """声明上下文引用协议。"""
        raise NotImplementedError


class ContextWindowPort(ABC):
    """上下文窗口端口。

    中文名称：上下文窗口端口。
    端口职责：定义上下文窗口和预算引用边界协议。
    输入输出边界：输入 ContextWindowRequest 与 TraceContext，输出 PortResult 包装的 ContextWindowResponse。
    所属 L1 层：上下文协议入口。
    不承担的实现职责：不计算 token，不裁剪内容，不压缩上下文。
    如何服务大模型执行力：为长链任务提供清晰可解释窗口边界。
    如何维持绝对边界：窗口只是声明，不释放额外信息。
    与后续 L2-L6 的关系：L3 可编排，L4 可实现真实适配。
    """

    @abstractmethod
    def declare_context_window(self, request: ContextWindowRequest, trace: TraceContext) -> PortResult[ContextWindowResponse]:
        """声明上下文窗口协议。"""
        raise NotImplementedError


class ContextAssemblyIntentPort(ABC):
    """上下文组装意图端口。

    中文名称：上下文组装意图端口。
    端口职责：定义上下文组装候选协议。
    输入输出边界：输入 ContextAssemblyIntentRequest 与 TraceContext，输出 PortResult 包装的 ContextAssemblyIntentResponse。
    所属 L1 层：上下文协议入口。
    不承担的实现职责：不拼接提示词，不调用模型，不读取真实内容。
    如何服务大模型执行力：让模型需要的上下文可以被结构化表达。
    如何维持绝对边界：组装只是意图，后续层必须检查边界。
    与后续 L2-L6 的关系：后续层可将其转入编排和适配流程。
    """

    @abstractmethod
    def submit_context_assembly_intent(self, request: ContextAssemblyIntentRequest, trace: TraceContext) -> PortResult[ContextAssemblyIntentResponse]:
        """声明上下文组装意图协议。"""
        raise NotImplementedError


class ContextBoundaryPort(ABC):
    """上下文边界端口。

    中文名称：上下文边界端口。
    端口职责：定义上下文可见、可引用和可使用边界协议。
    输入输出边界：输入 ContextBoundaryRequest 与 TraceContext，输出 PortResult 包装的 ContextBoundaryResponse。
    所属 L1 层：上下文协议入口。
    不承担的实现职责：不执行裁决，不过滤内容，不释放敏感信息。
    如何服务大模型执行力：以明确边界替代沉默阻断。
    如何维持绝对边界：边界声明不能绕过控制面。
    与后续 L2-L6 的关系：后续层可实现边界适配和插件隔离。
    """

    @abstractmethod
    def describe_context_boundary(self, request: ContextBoundaryRequest, trace: TraceContext) -> PortResult[ContextBoundaryResponse]:
        """声明上下文边界协议。"""
        raise NotImplementedError


class ContextCompressionHintPort(ABC):
    """上下文压缩提示端口。

    中文名称：上下文压缩提示端口。
    端口职责：定义上下文可能需要压缩或降噪的提示协议。
    输入输出边界：输入 ContextCompressionHintRequest 与 TraceContext，输出 PortResult 包装的 ContextCompressionHintResponse。
    所属 L1 层：上下文协议入口。
    不承担的实现职责：不执行压缩，不总结真实内容，不计算 token。
    如何服务大模型执行力：让长上下文问题成为后续可处理候选。
    如何维持绝对边界：提示不直接改变模型输入。
    与后续 L2-L6 的关系：第八阶段可验证，第 L3-L6 可实现具体策略。
    """

    @abstractmethod
    def submit_context_compression_hint(self, request: ContextCompressionHintRequest, trace: TraceContext) -> PortResult[ContextCompressionHintResponse]:
        """声明上下文压缩提示协议。"""
        raise NotImplementedError


class ContextCarryoverPort(ABC):
    """上下文延续端口。

    中文名称：上下文延续端口。
    端口职责：定义跨轮、跨任务、跨 Skill 的上下文延续协议。
    输入输出边界：输入 ContextCarryoverRequest 与 TraceContext，输出 PortResult 包装的 ContextCarryoverResponse。
    所属 L1 层：上下文协议入口。
    不承担的实现职责：不持久化会话，不拼接历史，不读取长期记忆。
    如何服务大模型执行力：保持长链任务的引用连续性。
    如何维持绝对边界：延续的是引用，不是无限制携带内容。
    与后续 L2-L6 的关系：后续层可实现会话状态和适配。
    """

    @abstractmethod
    def submit_context_carryover(self, request: ContextCarryoverRequest, trace: TraceContext) -> PortResult[ContextCarryoverResponse]:
        """声明上下文延续协议。"""
        raise NotImplementedError
