"""L1 Tool 工具端口协议。

本模块在 L1 中的职责：定义工具引用、工具说明、工具调用意图、工具输入边界、工具输出边界和工具观察结果端口。
本模块定义哪些端口：ToolReferencePort、ToolDescriptionPort、ToolInvocationIntentPort、ToolInputBoundaryPort、ToolOutputBoundaryPort、ToolObservationPort。
本模块不实现哪些能力：不实现真实工具加载、工具真实调用、真实工具执行、真实输入校验、真实输出清洗或真实观察采集。
本模块禁止事项：不得访问文件、网络、数据库、进程、真实工具系统、真实模型系统或插件系统。
本模块与 L2-L6 的关系：L2 可记录工具引用状态，L3 可编排工具意图，L4 可实现真实适配器，L5 可隔离插件工具，L6 可声明子系统工具观察。
本模块如何服务“大模型先看 Skill，再释放工具组”：工具端口只在 Skill 选中后的协议链中表达工具说明和意图，不让大模型直接看到内部端口结构。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.content import PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.metric import MetricRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef, ToolVersionRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ToolBoundary:
    """工具边界对象。

    作用：表达工具输入、输出、策略和风险边界。
    边界：只说明界限，不校验真实输入，不处理真实输出，不调用工具。
    """

    tool_ref: ToolRef
    boundary: PortBoundary
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolDescriptionView:
    """工具说明视图。

    作用：表达工具名称摘要、用途、输入输出边界和版本引用。
    边界：不包含真实函数、真实句柄或外部连接信息。
    """

    tool_ref: ToolRef
    summary: str
    input_boundary: ToolBoundary | None = None
    output_boundary: ToolBoundary | None = None
    version_ref: ToolVersionRef | VersionRef | None = None
    schema_ref: SchemaRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReferenceRequest:
    """工具引用请求。作用：声明需要引用的 ToolRef；边界：不加载工具。"""

    tool_ref: ToolRef
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReferenceResponse:
    """工具引用响应。作用：承载工具引用和版本事实；边界：不代表工具可调用。"""

    tool_ref: ToolRef
    version_ref: ToolVersionRef | VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolDescriptionRequest:
    """工具说明请求。作用：声明需要读取的工具说明；边界：不读取真实工具实现。"""

    tool_ref: ToolRef
    skill_ref: SkillRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolDescriptionResponse:
    """工具说明响应。作用：返回工具说明视图；边界：不包含真实执行入口。"""

    view: ToolDescriptionView
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolInvocationIntentRequest:
    """工具调用意图请求。

    作用：表达大模型想调用某个工具的意图和命令信封。
    边界：不得执行工具，不调用函数，不产生真实副作用。
    """

    tool_ref: ToolRef
    action_intent: ActionIntent
    command: CommandEnvelope | None = None
    skill_ref: SkillRef | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolInvocationIntentResponse:
    """工具调用意图响应。作用：承载意图引用、边界和验证引用；边界：不代表工具已被调用。"""

    tool_ref: ToolRef
    action_intent: ActionIntent
    signal_ref: SignalRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolInputBoundaryRequest:
    """工具输入边界请求。作用：声明工具输入载荷引用和边界上下文；边界：不校验真实输入。"""

    tool_ref: ToolRef
    payload_ref: PayloadRef | None = None
    boundary_context: PortBoundaryContext | None = None
    risk_view: RiskView | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolInputBoundaryResponse:
    """工具输入边界响应。作用：承载输入边界和越界事实；边界：不做真实安全裁决。"""

    boundary: ToolBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolOutputBoundaryRequest:
    """工具输出边界请求。作用：声明工具输出观察引用和边界上下文；边界：不清洗真实输出。"""

    tool_ref: ToolRef
    observation_ref: ObservationRef | None = None
    boundary_context: PortBoundaryContext | None = None
    risk_view: RiskView | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolOutputBoundaryResponse:
    """工具输出边界响应。作用：承载输出边界和越界事实；边界：不处理真实工具结果。"""

    boundary: ToolBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolObservationRequest:
    """工具观察请求。作用：声明工具观察结果引用；边界：不采集真实环境或真实工具结果。"""

    tool_ref: ToolRef
    observation_ref: ObservationRef
    metric_ref: MetricRef | None = None
    audit_ref: AuditRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolObservationResponse:
    """工具观察响应。作用：承载观察、指标、审计和证据引用；边界：不代表真实采集。"""

    observation_ref: ObservationRef
    metric_ref: MetricRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ToolReferencePort(ABC):
    """工具引用端口。

    中文名称：工具引用端口。
    端口职责：定义 ToolRef 的引用协议。
    输入输出边界：输入 ToolReferenceRequest 与 TraceContext，输出 PortResult 包装的 ToolReferenceResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不加载工具，不绑定真实工具句柄。
    如何服务大模型执行力：为 Skill 所需工具提供稳定引用。
    如何维持绝对边界：只返回引用事实，不触发工具动作。
    """

    @abstractmethod
    def reference_tool(self, request: ToolReferenceRequest, trace: TraceContext) -> PortResult[ToolReferenceResponse]:
        """声明工具引用协议。"""
        raise NotImplementedError


class ToolDescriptionPort(ABC):
    """工具说明端口。

    中文名称：工具说明端口。
    端口职责：定义工具名称、用途、输入输出边界的说明协议。
    输入输出边界：输入 ToolDescriptionRequest 与 TraceContext，输出 PortResult 包装的 ToolDescriptionResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不实现工具，不执行工具，不暴露真实句柄。
    如何服务大模型执行力：让大模型知道工具可用于 Skill 流程中的哪一步。
    如何维持绝对边界：工具说明只暴露可见边界，不暴露敏感实现。
    """

    @abstractmethod
    def describe_tool(self, request: ToolDescriptionRequest, trace: TraceContext) -> PortResult[ToolDescriptionResponse]:
        """声明工具说明协议。"""
        raise NotImplementedError


class ToolInvocationIntentPort(ABC):
    """工具调用意图端口。

    中文名称：工具调用意图端口。
    端口职责：定义大模型想调用工具时的意图表达协议。
    输入输出边界：输入 ToolInvocationIntentRequest 与 TraceContext，输出 PortResult 包装的 ToolInvocationIntentResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不调用函数，不执行工具，不产生副作用。
    如何服务大模型执行力：保留大模型主动发起工具意图的链路。
    如何维持绝对边界：意图必须先以协议对象表达，供边界层处理。
    """

    @abstractmethod
    def declare_tool_invocation_intent(
        self, request: ToolInvocationIntentRequest, trace: TraceContext
    ) -> PortResult[ToolInvocationIntentResponse]:
        """声明工具调用意图协议。"""
        raise NotImplementedError


class ToolInputBoundaryPort(ABC):
    """工具输入边界端口。

    中文名称：工具输入边界端口。
    端口职责：定义工具输入边界说明协议。
    输入输出边界：输入 ToolInputBoundaryRequest 与 TraceContext，输出 PortResult 包装的 ToolInputBoundaryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不校验真实输入，不做真实安全裁决。
    如何服务大模型执行力：让大模型知道输入形状和约束。
    如何维持绝对边界：输入边界用结构化对象携带越界事实。
    """

    @abstractmethod
    def describe_tool_input_boundary(
        self, request: ToolInputBoundaryRequest, trace: TraceContext
    ) -> PortResult[ToolInputBoundaryResponse]:
        """声明工具输入边界协议。"""
        raise NotImplementedError


class ToolOutputBoundaryPort(ABC):
    """工具输出边界端口。

    中文名称：工具输出边界端口。
    端口职责：定义工具输出边界说明协议。
    输入输出边界：输入 ToolOutputBoundaryRequest 与 TraceContext，输出 PortResult 包装的 ToolOutputBoundaryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不处理真实输出，不清洗真实数据。
    如何服务大模型执行力：让工具观察结果可被大模型安全理解。
    如何维持绝对边界：输出边界与越界事实显式返回。
    """

    @abstractmethod
    def describe_tool_output_boundary(
        self, request: ToolOutputBoundaryRequest, trace: TraceContext
    ) -> PortResult[ToolOutputBoundaryResponse]:
        """声明工具输出边界协议。"""
        raise NotImplementedError


class ToolObservationPort(ABC):
    """工具观察端口。

    中文名称：工具观察端口。
    端口职责：定义工具观察结果返回给大模型的协议。
    输入输出边界：输入 ToolObservationRequest 与 TraceContext，输出 PortResult 包装的 ToolObservationResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不采集真实观察，不执行工具，不读取外部环境。
    如何服务大模型执行力：把后续工具适配器结果以观察引用传回大模型。
    如何维持绝对边界：观察只以 L0 引用表达，不携带真实资源句柄。
    """

    @abstractmethod
    def submit_tool_observation(self, request: ToolObservationRequest, trace: TraceContext) -> PortResult[ToolObservationResponse]:
        """声明工具观察结果协议。"""
        raise NotImplementedError
