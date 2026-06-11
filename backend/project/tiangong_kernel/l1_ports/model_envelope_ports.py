"""L1 模型信封端口协议。

本模块在 L1 中的职责：定义模型请求、响应、工具调用意图、观察回传和错误回传的信封协议。
本模块定义哪些端口：ModelRequestEnvelopePort、ModelResponseEnvelopePort、ModelToolCallEnvelopePort、ModelObservationEnvelopePort、ModelErrorEnvelopePort。
本模块不实现哪些能力：不实现真实模型会话、真实模型接口调用、真实上下文拼接、真实工具协议转换、真实重试或真实恢复算法。
本模块禁止事项：不得导入模型供应方库，不得持有真实认证材料，不得访问文件、网络、数据库、工具系统或插件系统。
本模块与 L2-L6 的关系：L2 可记录模型信封状态，L3 可编排信封流转，L4 可实现真实模型适配，L5 可约束插件信封边界，L6 可提交子系统反馈信封。
本模块如何服务“大模型直接控制智能体”：只提供输入输出外壳，让大模型的 Skill 选择、工具调用意图、观察需求和失败反馈有稳定结构。
本模块如何为自我学习、自我迭代、自我进化提供反馈入口：只把失败、观察、错误和意图保存为引用事实，供后续阶段作为候选证据，不直接触发真实修改。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.errors import CoreError
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.message import MessageRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_result import PortResult
from .tool_release_ports import ToolReleaseView


@dataclass(frozen=True, slots=True)
class ModelRequestEnvelope:
    """模型请求信封。

    作用：表达进入模型边界的请求来源、追踪、参与者、内容引用、可见 Skill、可见工具组和边界说明。
    边界：不发起真实模型请求，不读取内容，不拼接上下文，不构造提示词。
    """

    request_id: RefId
    trace_context: TraceContext
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    conversation_message_refs: tuple[MessageRef, ...] = field(default_factory=tuple)
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    payload_refs: tuple[PayloadRef, ...] = field(default_factory=tuple)
    visible_skill_refs: tuple[SkillRef, ...] = field(default_factory=tuple)
    visible_tool_group_refs: tuple[ResourceRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelResponseEnvelope:
    """模型响应信封。

    作用：表达模型文本输出引用、结构化行动意图、Skill 选择意图、工具调用意图、失败反馈和观察需求。
    边界：不执行任何动作，不选择 Skill，不调用工具，不触发真实副作用。
    """

    response_id: RefId
    request_id: RefId | None = None
    message_ref: MessageRef | None = None
    output_content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    output_payload_refs: tuple[PayloadRef, ...] = field(default_factory=tuple)
    action_intents: tuple[ActionIntent, ...] = field(default_factory=tuple)
    selected_skill_refs: tuple[SkillRef, ...] = field(default_factory=tuple)
    tool_call_relation_refs: tuple[RelationRef, ...] = field(default_factory=tuple)
    failure_signal_refs: tuple[SignalRef, ...] = field(default_factory=tuple)
    observation_request_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolCallEnvelope:
    """模型工具调用意图信封。

    作用：表达大模型想调用某个工具的结构化意图、所属 Skill、工具组、载荷和边界上下文。
    边界：不是工具执行器，不释放工具，不调用函数，不产生真实副作用。
    """

    envelope_id: RefId
    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    tool_group_ref: ResourceRef | None = None
    action_intent: ActionIntent | None = None
    payload_ref: PayloadRef | None = None
    relation_ref: RelationRef | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelObservationEnvelope:
    """模型观察信封。

    作用：把 ObservationRef、EvidenceRef、AuditRef、内容引用和工具释放视图引用组织成可回传模型的结构。
    边界：不读取观察内容，不做摘要算法，不做清洗算法，不验证真实结果。
    """

    envelope_id: RefId
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[AuditRef, ...] = field(default_factory=tuple)
    content_refs: tuple[ContentRef, ...] = field(default_factory=tuple)
    payload_refs: tuple[PayloadRef, ...] = field(default_factory=tuple)
    tool_release_views: tuple[ToolReleaseView, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelErrorEnvelope:
    """模型错误信封。

    作用：表达模型错误、端口错误或边界错误进入模型上下文时需要携带的错误事实与可替代路径引用。
    边界：不执行错误恢复，不自动重试，不修改系统状态。
    """

    envelope_id: RefId
    error: CoreError | None = None
    related_request_id: RefId | None = None
    related_response_id: RefId | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelRequestEnvelopeRequest:
    """模型请求信封声明请求。作用：声明请求信封结构；边界：不发起模型请求。"""

    envelope: ModelRequestEnvelope
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelRequestEnvelopeResponse:
    """模型请求信封声明响应。作用：返回请求信封和证据引用；边界：不代表真实请求已发送。"""

    envelope: ModelRequestEnvelope
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelResponseEnvelopeRequest:
    """模型响应信封声明请求。作用：声明模型响应信封结构；边界：不执行响应中的动作意图。"""

    envelope: ModelResponseEnvelope
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelResponseEnvelopeResponse:
    """模型响应信封声明响应。作用：返回响应信封和审计引用；边界：不代表动作已被执行。"""

    envelope: ModelResponseEnvelope
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolCallEnvelopeRequest:
    """模型工具调用信封请求。作用：声明模型工具调用意图；边界：不执行工具。"""

    envelope: ModelToolCallEnvelope
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelToolCallEnvelopeResponse:
    """模型工具调用信封响应。作用：返回工具调用意图信封；边界：不释放工具、不调用函数。"""

    envelope: ModelToolCallEnvelope
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelObservationEnvelopeRequest:
    """模型观察信封请求。作用：声明观察引用如何回传模型；边界：不读取观察内容。"""

    envelope: ModelObservationEnvelope
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelObservationEnvelopeResponse:
    """模型观察信封响应。作用：返回观察信封和证据引用；边界：不做摘要或清洗。"""

    envelope: ModelObservationEnvelope
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelErrorEnvelopeRequest:
    """模型错误信封请求。作用：声明错误事实如何进入模型上下文；边界：不执行恢复。"""

    envelope: ModelErrorEnvelope
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ModelErrorEnvelopeResponse:
    """模型错误信封响应。作用：返回错误信封和审计引用；边界：不自动重试。"""

    envelope: ModelErrorEnvelope
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ModelRequestEnvelopePort(ABC):
    """模型请求信封端口。

    中文名称：模型请求信封端口。
    端口职责：定义模型请求信封的声明协议。
    输入输出边界：输入 ModelRequestEnvelopeRequest 与 TraceContext，输出 PortResult 包装的 ModelRequestEnvelopeResponse。
    所属 L1 层：模型端口协议层。
    不承担的实现职责：不调用模型，不拼接上下文，不构造提示词。
    如何服务大模型执行力：让大模型可见 Skill、工具组和边界说明形成稳定输入结构。
    如何维持绝对边界：只传递引用和边界上下文，不携带真实资源句柄。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：可作为后续分析模型输入证据。
    """

    @abstractmethod
    def declare_model_request_envelope(
        self, request: ModelRequestEnvelopeRequest, trace: TraceContext
    ) -> PortResult[ModelRequestEnvelopeResponse]:
        """声明模型请求信封协议。"""
        raise NotImplementedError


class ModelResponseEnvelopePort(ABC):
    """模型响应信封端口。

    中文名称：模型响应信封端口。
    端口职责：定义模型响应信封的声明协议。
    输入输出边界：输入 ModelResponseEnvelopeRequest 与 TraceContext，输出 PortResult 包装的 ModelResponseEnvelopeResponse。
    所属 L1 层：模型端口协议层。
    不承担的实现职责：不执行响应动作，不替模型选择 Skill，不调用工具。
    如何服务大模型执行力：把文本、Skill 选择意图和工具调用意图统一表达。
    如何维持绝对边界：响应信封只是意图和引用，不产生真实副作用。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：失败反馈和观察需求可成为候选证据。
    """

    @abstractmethod
    def declare_model_response_envelope(
        self, request: ModelResponseEnvelopeRequest, trace: TraceContext
    ) -> PortResult[ModelResponseEnvelopeResponse]:
        """声明模型响应信封协议。"""
        raise NotImplementedError


class ModelToolCallEnvelopePort(ABC):
    """模型工具调用意图信封端口。

    中文名称：模型工具调用意图信封端口。
    端口职责：定义大模型想调用工具时的结构化意图信封。
    输入输出边界：输入 ModelToolCallEnvelopeRequest 与 TraceContext，输出 PortResult 包装的 ModelToolCallEnvelopeResponse。
    所属 L1 层：模型端口协议层。
    不承担的实现职责：不执行工具，不释放工具，不生成真实副作用。
    如何服务大模型执行力：让大模型按 Skill 流程表达工具使用意图。
    如何维持绝对边界：工具调用仍只是信封，后续边界和执行面另行处理。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：工具不足或失败可被后续反馈端口引用。
    """

    @abstractmethod
    def declare_model_tool_call_envelope(
        self, request: ModelToolCallEnvelopeRequest, trace: TraceContext
    ) -> PortResult[ModelToolCallEnvelopeResponse]:
        """声明模型工具调用意图信封协议。"""
        raise NotImplementedError


class ModelObservationEnvelopePort(ABC):
    """模型观察信封端口。

    中文名称：模型观察信封端口。
    端口职责：定义观察结果进入模型上下文的信封协议。
    输入输出边界：输入 ModelObservationEnvelopeRequest 与 TraceContext，输出 PortResult 包装的 ModelObservationEnvelopeResponse。
    所属 L1 层：模型端口协议层。
    不承担的实现职责：不读取观察内容，不做摘要算法，不做清洗算法。
    如何服务大模型执行力：把工具或系统观察以引用形式回传给大模型继续判断。
    如何维持绝对边界：观察只以 Ref 传递，不读取真实材料。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：观察引用可成为后续学习与评估证据。
    """

    @abstractmethod
    def declare_model_observation_envelope(
        self, request: ModelObservationEnvelopeRequest, trace: TraceContext
    ) -> PortResult[ModelObservationEnvelopeResponse]:
        """声明模型观察信封协议。"""
        raise NotImplementedError


class ModelErrorEnvelopePort(ABC):
    """模型错误信封端口。

    中文名称：模型错误信封端口。
    端口职责：定义错误事实进入模型上下文的信封协议。
    输入输出边界：输入 ModelErrorEnvelopeRequest 与 TraceContext，输出 PortResult 包装的 ModelErrorEnvelopeResponse。
    所属 L1 层：模型端口协议层。
    不承担的实现职责：不执行恢复算法，不自动重试，不修改系统。
    如何服务大模型执行力：让边界错误和端口错误以可理解结构返回模型。
    如何维持绝对边界：错误信封只提供原因与替代路径引用，不绕过边界。
    是否与后续自我学习 / 自我迭代 / 自我进化有关：错误事实可成为修正和迭代证据。
    """

    @abstractmethod
    def declare_model_error_envelope(
        self, request: ModelErrorEnvelopeRequest, trace: TraceContext
    ) -> PortResult[ModelErrorEnvelopeResponse]:
        """声明模型错误信封协议。"""
        raise NotImplementedError
