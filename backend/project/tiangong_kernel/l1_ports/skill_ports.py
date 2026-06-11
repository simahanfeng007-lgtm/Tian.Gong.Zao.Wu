"""L1 Skill 直显端口协议。

本模块在 L1 中的职责：定义 Skill 引用、注册、查询、暴露、流程说明和使用边界端口。
本模块定义哪些端口：SkillReferencePort、SkillRegistryPort、SkillQueryPort、SkillExposurePort、SkillFlowPort、SkillBoundaryPort。
本模块不实现哪些能力：不实现真实 Skill 注册表、真实 Skill 查询算法、真实 Skill 展示算法、真实工具释放、工具真实调用或模型真实调用。
本模块禁止事项：不得访问文件、网络、数据库、插件目录、真实工具系统或真实模型系统。
本模块与 L2-L6 的关系：L2 可记录 Skill 状态，L3 可编排 Skill 选择后的协议流，L4 可实现外部适配，L5 可管理插件隔离，L6 可提供子系统 Skill 声明。
本模块如何服务“大模型先看 Skill，再释放工具组”：只定义大模型可见的 Skill 说明边界，不暴露内部端口，不释放工具组，让后续控制面和执行面保持清晰分层。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class SkillBoundary:
    """Skill 使用边界对象。

    作用：表达某个 Skill 的可用范围、禁用范围、策略引用和风险视图。
    边界：只描述 Skill 使用界限，不做真实裁决、不评分、不触发工具组释放。
    """

    skill_ref: SkillRef
    boundary: PortBoundary
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    contract_ref: ContractRef | None = None
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillExposureView:
    """Skill 暴露视图。

    作用：表达大模型可见的 Skill 摘要、流程引用、工具组引用和边界上下文。
    边界：不暴露内部端口结构，不暴露真实工具实现，不调用模型。
    """

    skill_ref: SkillRef
    summary: str
    flow_ref: RelationRef | None = None
    tool_group_ref: ResourceRef | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillFlowView:
    """Skill 流程视图。

    作用：表达 Skill 的目标、计划、行动意图、所需工具引用和失败反馈信号。
    边界：只说明流程，不执行流程，不调用工具，不调度任务。
    """

    skill_ref: SkillRef
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    action_intents: tuple[ActionIntent, ...] = field(default_factory=tuple)
    required_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    failure_signal_ref: SignalRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillReferenceRequest:
    """Skill 引用请求。作用：声明需要引用的 Skill 与命名空间；边界：不加载 Skill 内容。"""

    skill_ref: SkillRef
    namespace_ref: NamespaceRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillReferenceResponse:
    """Skill 引用响应。作用：返回 Skill、版本、结构和证据引用；边界：不代表真实注册存在。"""

    skill_ref: SkillRef
    version_ref: VersionRef | None = None
    schema_ref: SchemaRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillRegistryRequest:
    """Skill 注册请求。作用：表达注册意图和边界上下文；边界：不写注册表、不写数据库、不加载插件。"""

    skill_ref: SkillRef
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillRegistryResponse:
    """Skill 注册响应。作用：表达注册协议结果引用；边界：不代表真实持久化。"""

    skill_ref: SkillRef
    audit_ref: AuditRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillQueryRequest:
    """Skill 查询请求。作用：声明查询信封、调用者和范围；边界：不实现检索、排序或模型筛选。"""

    query: QueryEnvelope
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillQueryResponse:
    """Skill 查询响应。作用：承载候选 Skill 引用集合；边界：不代表真实排序或最终选择。"""

    skill_refs: tuple[SkillRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillExposureRequest:
    """Skill 暴露请求。作用：声明需要给大模型可见的 Skill 说明范围；边界：不暴露内部端口。"""

    skill_refs: tuple[SkillRef, ...] = field(default_factory=tuple)
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillExposureResponse:
    """Skill 暴露响应。作用：承载大模型可见的 Skill 说明视图；边界：不包含真实工具句柄。"""

    views: tuple[SkillExposureView, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillFlowRequest:
    """Skill 流程请求。作用：声明需要读取的 Skill 流程说明；边界：不执行流程。"""

    skill_ref: SkillRef
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillFlowResponse:
    """Skill 流程响应。作用：承载 Skill 流程视图；边界：不产生真实行动。"""

    view: SkillFlowView
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillBoundaryRequest:
    """Skill 边界请求。作用：声明需要说明的 Skill 使用边界；边界：不做真实安全裁决。"""

    skill_ref: SkillRef
    risk_view: RiskView | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillBoundaryResponse:
    """Skill 边界响应。作用：承载 Skill 边界和越界事实；边界：不阻断、不审批、不释放工具组。"""

    boundary: SkillBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class SkillReferencePort(ABC):
    """Skill 引用端口。

    中文名称：Skill 引用端口。
    端口职责：定义 SkillRef 的引用、版本和证据返回协议。
    输入输出边界：输入 SkillReferenceRequest 与 TraceContext，输出 PortResult 包装的 SkillReferenceResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不创建 Skill、不加载 Skill、不执行 Skill。
    如何服务大模型执行力：为大模型可理解的 Skill 入口提供稳定引用。
    如何维持绝对边界：只返回引用事实，不泄露内部实现或工具句柄。
    """

    @abstractmethod
    def reference_skill(self, request: SkillReferenceRequest, trace: TraceContext) -> PortResult[SkillReferenceResponse]:
        """声明 Skill 引用协议。"""
        raise NotImplementedError


class SkillRegistryPort(ABC):
    """Skill 注册端口。

    中文名称：Skill 注册端口。
    端口职责：定义 Skill 注册请求和注册结果引用协议。
    输入输出边界：输入 SkillRegistryRequest 与 TraceContext，输出 PortResult 包装的 SkillRegistryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不维护真实注册表，不写文件，不加载插件。
    如何服务大模型执行力：让后续层可声明 Skill 进入可见集合的协议入口。
    如何维持绝对边界：注册只表达意图和引用，不产生外部副作用。
    """

    @abstractmethod
    def register_skill(self, request: SkillRegistryRequest, trace: TraceContext) -> PortResult[SkillRegistryResponse]:
        """声明 Skill 注册协议。"""
        raise NotImplementedError


class SkillQueryPort(ABC):
    """Skill 查询端口。

    中文名称：Skill 查询端口。
    端口职责：定义 Skill 查询条件与候选引用返回协议。
    输入输出边界：输入 SkillQueryRequest 与 TraceContext，输出 PortResult 包装的 SkillQueryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不实现检索、排序、召回、模型选择或上下文拼接算法。
    如何服务大模型执行力：为大模型后续看到合适 Skill 提供协议形状。
    如何维持绝对边界：查询只返回引用集合，不越过边界释放工具。
    """

    @abstractmethod
    def query_skills(self, request: SkillQueryRequest, trace: TraceContext) -> PortResult[SkillQueryResponse]:
        """声明 Skill 查询协议。"""
        raise NotImplementedError


class SkillExposurePort(ABC):
    """Skill 暴露端口。

    中文名称：Skill 暴露端口。
    端口职责：定义大模型可见 Skill 说明的输出边界。
    输入输出边界：输入 SkillExposureRequest 与 TraceContext，输出 PortResult 包装的 SkillExposureResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不暴露内部 Port，不暴露工具实现，不调用模型。
    如何服务大模型执行力：让大模型先理解 Skill 目标、流程和边界。
    如何维持绝对边界：只暴露经过协议约束的说明视图。
    """

    @abstractmethod
    def expose_skills(self, request: SkillExposureRequest, trace: TraceContext) -> PortResult[SkillExposureResponse]:
        """声明 Skill 暴露协议。"""
        raise NotImplementedError


class SkillFlowPort(ABC):
    """Skill 流程端口。

    中文名称：Skill 流程端口。
    端口职责：定义 Skill 工作流程、输入要求、输出结果和失败反馈格式。
    输入输出边界：输入 SkillFlowRequest 与 TraceContext，输出 PortResult 包装的 SkillFlowResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不执行流程，不调度工具，不生成真实计划。
    如何服务大模型执行力：把做事步骤作为可见知识动作单元提供给大模型。
    如何维持绝对边界：流程只说明，不越界触发真实动作。
    """

    @abstractmethod
    def describe_skill_flow(self, request: SkillFlowRequest, trace: TraceContext) -> PortResult[SkillFlowResponse]:
        """声明 Skill 流程说明协议。"""
        raise NotImplementedError


class SkillBoundaryPort(ABC):
    """Skill 边界端口。

    中文名称：Skill 边界端口。
    端口职责：定义 Skill 可用范围、禁用范围和风险边界说明协议。
    输入输出边界：输入 SkillBoundaryRequest 与 TraceContext，输出 PortResult 包装的 SkillBoundaryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不做真实风险评分，不做最终裁决，不释放工具组。
    如何服务大模型执行力：让大模型知道 Skill 可安全使用的范围。
    如何维持绝对边界：边界说明与越界事实可被后续层追踪。
    """

    @abstractmethod
    def describe_skill_boundary(self, request: SkillBoundaryRequest, trace: TraceContext) -> PortResult[SkillBoundaryResponse]:
        """声明 Skill 边界说明协议。"""
        raise NotImplementedError
