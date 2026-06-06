"""L1 模型抽象端口协议。

本模块在 L1 中的职责：定义模型、模型会话、模型消息、模型上下文和模型可见行动视图的抽象端口。
本模块定义哪些端口：ModelPort、ModelSessionPort、ModelMessagePort、ModelContextPort、ModelAvailableActionViewPort。
本模块不实现哪些能力：不实现真实模型接口调用、真实模型会话、真实模型路由、真实上下文拼接、真实 Skill 选择或工具真实调用。
本模块禁止事项：不得导入模型供应方库，不得持有真实认证材料，不得访问文件、网络、数据库、真实工具系统或插件系统。
本模块与 L2-L6 的关系：L2 可保存模型边界状态，L3 可编排模型信封流，L4 可实现外部模型适配，L5 可约束插件模型边界，L6 可把子系统反馈提交到模型上下文。
本模块如何服务“大模型直接控制智能体”：模型端口只稳定表达输入输出与可见行动，不替大模型思考，不替大模型选择 Skill，不把大模型困在复杂审批链里。
本模块如何为自我学习、自我迭代、自我进化提供反馈入口：模型输出、失败和反思只作为引用证据进入后续候选流程，本模块不执行真实学习、迭代或进化。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.communication import ChannelRef, ConversationRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.message import MessageRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .model_envelope_ports import ModelErrorEnvelope, ModelRequestEnvelope, ModelResponseEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult
from .skill_ports import SkillExposureView, SkillFlowView
from .tool_release_ports import ToolReleaseView


@dataclass(frozen=True, slots=True)
class ModelSessionBoundary:
    """模型会话边界对象。

    作用：表达模型会话引用、通道、会话链、作用域和边界说明。
    边界：不创建真实模型会话，不保存真实上下文，不持有真实资源句柄。
    """

    session_ref: ResourceRef
    boundary: PortBoundary
    channel_ref: ChannelRef | None = None
    conversation_ref: ConversationRef | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSkillView:
    """模型可见 Skill 视图。

    作用：表达大模型当前可见的 Skill 说明和流程引用。
    边界：不选择 Skill，不暴露内部端口，不加载真实 Skill 内容。
    """

    skill_ref: SkillRef
    exposure_view: SkillExposureView | None = None
    flow_view: SkillFlowView | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolGroupView:
    """模型可见工具组视图。

    作用：表达 Skill 被选择后大模型可见的工具组释放视图。
    边界：不释放工具，不暴露真实工具实现，不执行撤销或租约逻辑。
    """

    tool_group_ref: ResourceRef
    release_view: ToolReleaseView | None = None
    visible_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelAvailableActionView:
    """模型可见行动视图。

    作用：表达模型当前可见的 Skill、工具组、观察引用、边界说明和风险视图。
    边界：只是可见行动边界，不是旧体系对象，不执行工具或裁决。
    """

    skill_views: tuple[ModelSkillView, ...] = field(default_factory=tuple)
    tool_group_views: tuple[ModelToolGroupView, ...] = field(default_factory=tuple)
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    risk_view: RiskView | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelContextView:
    """模型上下文视图。

    作用：表达可供模型使用的内容、载荷、消息、Skill、观察、历史和边界引用。
    边界：不拼接真实上下文，不压缩内容，不读取真实记忆或文件。
    """

    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    payload_refs: tuple[PayloadRef, ...] = field(default_factory=tuple)
    message_refs: tuple[MessageRef, ...] = field(default_factory=tuple)
    skill_views: tuple[ModelSkillView, ...] = field(default_factory=tuple)
    tool_group_views: tuple[ModelToolGroupView, ...] = field(default_factory=tuple)
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    relation_refs: tuple[RelationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelObservationView:
    """模型观察视图。

    作用：表达模型侧可见的观察、证据和审计引用。
    边界：不采集观察，不读取观察详情，不做真实验收。
    """

    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[AuditRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """模型抽象请求。作用：声明模型请求信封和上下文视图；边界：不调用真实模型。"""

    request_envelope: ModelRequestEnvelope
    context_view: ModelContextView | None = None
    action_view: ModelAvailableActionView | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """模型抽象响应。作用：承载模型响应信封或错误信封；边界：不执行响应内容。"""

    response_envelope: ModelResponseEnvelope | None = None
    error_envelope: ModelErrorEnvelope | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSessionRequest:
    """模型会话请求。作用：声明模型会话边界；边界：不创建真实会话。"""

    session_boundary: ModelSessionBoundary
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelSessionResponse:
    """模型会话响应。作用：返回模型会话边界和证据引用；边界：不保存上下文。"""

    session_boundary: ModelSessionBoundary
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelMessageRequest:
    """模型消息请求。作用：声明模型输入、输出或观察消息引用；边界：不发送消息。"""

    message_ref: MessageRef
    conversation_ref: ConversationRef | None = None
    payload_ref: PayloadRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelMessageResponse:
    """模型消息响应。作用：返回模型消息引用和内容引用；边界：不调用聊天接口。"""

    message_ref: MessageRef
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    payload_refs: tuple[PayloadRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelContextRequest:
    """模型上下文请求。作用：声明模型上下文视图；边界：不拼接或压缩真实上下文。"""

    context_view: ModelContextView
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelContextResponse:
    """模型上下文响应。作用：返回上下文视图和证据引用；边界：不读取真实记忆。"""

    context_view: ModelContextView
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelAvailableActionViewRequest:
    """模型可见行动视图请求。作用：声明模型可见 Skill、工具组和边界；边界：不选择 Skill。"""

    action_view: ModelAvailableActionView
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelAvailableActionViewResponse:
    """模型可见行动视图响应。作用：返回可见行动视图；边界：不释放工具组。"""

    action_view: ModelAvailableActionView
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ModelPort(ABC):
    """模型端口。

    中文名称：模型端口。
    端口职责：定义模型输入输出协议边界。
    输入输出边界：输入 ModelRequestEnvelope 与 TraceContext，输出 PortResult 包装的 ModelResponse。
    所属 L1 层：模型抽象端口协议。
    不承担的实现职责：不调用真实模型，不持有真实认证材料，不决定 Skill 或工具调用。
    如何服务大模型执行力：把模型输入输出保持为清晰协议，让大模型继续承担理解与行动主控。
    如何维持绝对边界：端口只传递信封和引用，不绕过边界层与工具组释放协议。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：模型响应可被反馈和反思端口作为证据引用。
    """

    @abstractmethod
    def request_model_response(self, request: ModelRequestEnvelope, trace: TraceContext) -> PortResult[ModelResponse]:
        """声明模型响应请求协议。"""
        raise NotImplementedError


class ModelSessionPort(ABC):
    """模型会话端口。

    中文名称：模型会话端口。
    端口职责：定义模型会话引用与生命周期边界协议。
    输入输出边界：输入 ModelSessionRequest 与 TraceContext，输出 PortResult 包装的 ModelSessionResponse。
    所属 L1 层：模型抽象端口协议。
    不承担的实现职责：不创建真实会话，不保存真实上下文，不管理连接。
    如何服务大模型执行力：为连续任务提供可引用的会话边界事实。
    如何维持绝对边界：会话只是一组引用和边界说明，不包含真实资源句柄。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：会话边界可帮助后续归因模型反馈来源。
    """

    @abstractmethod
    def describe_model_session(
        self, request: ModelSessionRequest, trace: TraceContext
    ) -> PortResult[ModelSessionResponse]:
        """声明模型会话边界协议。"""
        raise NotImplementedError


class ModelMessagePort(ABC):
    """模型消息端口。

    中文名称：模型消息端口。
    端口职责：定义模型输入消息、输出消息和观察消息的引用协议。
    输入输出边界：输入 ModelMessageRequest 与 TraceContext，输出 PortResult 包装的 ModelMessageResponse。
    所属 L1 层：模型抽象端口协议。
    不承担的实现职责：不发送消息，不调用聊天接口，不拼接对话历史。
    如何服务大模型执行力：让模型消息在系统中有稳定引用，便于观察回传和失败归因。
    如何维持绝对边界：消息只以 L0 引用表达，不读取真实内容。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：消息引用可作为后续修正提示的证据。
    """

    @abstractmethod
    def describe_model_message(
        self, request: ModelMessageRequest, trace: TraceContext
    ) -> PortResult[ModelMessageResponse]:
        """声明模型消息协议。"""
        raise NotImplementedError


class ModelContextPort(ABC):
    """模型上下文端口。

    中文名称：模型上下文端口。
    端口职责：定义模型可用上下文边界协议。
    输入输出边界：输入 ModelContextRequest 与 TraceContext，输出 PortResult 包装的 ModelContextResponse。
    所属 L1 层：模型抽象端口协议。
    不承担的实现职责：不压缩上下文，不读取文件或记忆，不构造提示词。
    如何服务大模型执行力：把 Skill、工具组、观察和历史引用整理为可见边界。
    如何维持绝对边界：上下文只承载引用和边界说明，不暴露内部实现。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：上下文视图可用于后续分析模型行为原因。
    """

    @abstractmethod
    def describe_model_context(
        self, request: ModelContextRequest, trace: TraceContext
    ) -> PortResult[ModelContextResponse]:
        """声明模型上下文边界协议。"""
        raise NotImplementedError


class ModelAvailableActionViewPort(ABC):
    """模型可见行动视图端口。

    中文名称：模型可见行动视图端口。
    端口职责：定义模型当前可见 Skill、工具组、观察和边界说明的视图协议。
    输入输出边界：输入 ModelAvailableActionViewRequest 与 TraceContext，输出 PortResult 包装的 ModelAvailableActionViewResponse。
    所属 L1 层：模型抽象端口协议。
    不承担的实现职责：不选择 Skill，不释放工具，不执行安全裁决。
    如何服务大模型执行力：让大模型清楚知道当前可用行动范围，而不是隐藏可执行路径。
    如何维持绝对边界：视图只展示已进入边界内的引用，不暴露内部端口或真实工具实现。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：可用于解释模型为何选择某个 Skill 或工具组。
    """

    @abstractmethod
    def describe_available_action_view(
        self, request: ModelAvailableActionViewRequest, trace: TraceContext
    ) -> PortResult[ModelAvailableActionViewResponse]:
        """声明模型可见行动视图协议。"""
        raise NotImplementedError
