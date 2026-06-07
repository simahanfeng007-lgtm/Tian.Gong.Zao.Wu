"""L1 ToolBinding 工具绑定端口协议。

本模块在 L1 中的职责：定义 Skill 与工具、Skill 与工具组、工具依赖、工具使用流程之间的绑定协议。
本模块定义哪些端口：SkillToolBindingPort、ToolGroupBindingPort、ToolDependencyPort、ToolUsageFlowPort。
本模块不实现哪些能力：不实现真实绑定存储、真实依赖检查、真实工具流程执行或真实工具加载。
本模块禁止事项：不得写注册表、访问文件、访问数据库、扫描插件、调用工具或改变全局状态。
本模块与 L2-L6 的关系：L2 可记录绑定状态，L3 可编排工具使用流程，L4 可实现适配器绑定，L5 可隔离插件绑定，L6 可声明子系统工具依赖。
本模块如何服务“大模型先看 Skill，再释放工具组”：绑定协议说明 Skill、工具组和工具之间的关系，让工具组释放前后的可见范围有结构依据。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.relation import DependencyRef, RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class SkillToolBindingView:
    """Skill 与工具绑定视图。

    作用：表达一个 Skill 与一个或多个工具引用之间的关系。
    边界：只表达关系，不写入注册表，不加载工具，不执行工具。
    """

    skill_ref: SkillRef
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    relation_ref: RelationRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupBindingView:
    """Skill 与工具组绑定视图。

    作用：表达 Skill 与工具组资源引用之间的绑定关系。
    边界：不实现真实绑定存储，不释放工具组。
    """

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    relation_ref: RelationRef | None = None
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolUsageFlowView:
    """工具使用流程视图。

    作用：表达工具调用顺序、可并行性、依赖引用和失败反馈信号。
    边界：只说明流程，不执行流程，不做依赖算法。
    """

    skill_ref: SkillRef
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    dependency_refs: tuple[DependencyRef, ...] = field(default_factory=tuple)
    action_intents: tuple[ActionIntent, ...] = field(default_factory=tuple)
    plan_ref: PlanRef | None = None
    failure_signal_ref: SignalRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillToolBindingRequest:
    """Skill 工具绑定请求。作用：声明 Skill 与工具引用关系；边界：不执行绑定写入。"""

    skill_ref: SkillRef
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    relation_ref: RelationRef | None = None
    query: QueryEnvelope | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillToolBindingResponse:
    """Skill 工具绑定响应。作用：承载绑定视图和验证引用；边界：不代表真实持久化。"""

    view: SkillToolBindingView
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupBindingRequest:
    """工具组绑定请求。作用：声明 Skill 与工具组资源之间的关系；边界：不改注册表。"""

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    relation_ref: RelationRef | None = None
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupBindingResponse:
    """工具组绑定响应。作用：承载工具组绑定视图；边界：不释放工具组。"""

    view: ToolGroupBindingView
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolDependencyRequest:
    """工具依赖请求。作用：声明工具间依赖关系和观察引用；边界：不执行依赖检查算法。"""

    dependency_ref: DependencyRef
    source_tool_ref: ToolRef | None = None
    target_tool_ref: ToolRef | None = None
    required_observation_ref: ObservationRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolDependencyResponse:
    """工具依赖响应。作用：承载依赖引用和越界事实；边界：不阻断真实流程。"""

    dependency_ref: DependencyRef
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolUsageFlowRequest:
    """工具使用流程请求。作用：声明 Skill 下工具调用顺序、依赖和失败反馈；边界：不执行流程。"""

    skill_ref: SkillRef
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    dependency_refs: tuple[DependencyRef, ...] = field(default_factory=tuple)
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolUsageFlowResponse:
    """工具使用流程响应。作用：承载工具使用流程视图；边界：不触发工具调用。"""

    view: ToolUsageFlowView
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class SkillToolBindingPort(ABC):
    """Skill 工具绑定端口。

    中文名称：Skill 工具绑定端口。
    端口职责：定义 Skill 与工具引用之间的绑定协议。
    输入输出边界：输入 SkillToolBindingRequest 与 TraceContext，输出 PortResult 包装的 SkillToolBindingResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不写注册表，不加载工具，不执行绑定副作用。
    如何服务大模型执行力：让 Skill 流程能说明需要哪些工具。
    如何维持绝对边界：绑定只表达引用关系，不触发工具动作。
    """

    @abstractmethod
    def describe_skill_tool_binding(
        self, request: SkillToolBindingRequest, trace: TraceContext
    ) -> PortResult[SkillToolBindingResponse]:
        """声明 Skill 工具绑定协议。"""
        raise NotImplementedError


class ToolGroupBindingPort(ABC):
    """工具组绑定端口。

    中文名称：工具组绑定端口。
    端口职责：定义 Skill 与工具组之间的绑定协议。
    输入输出边界：输入 ToolGroupBindingRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupBindingResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不实现真实绑定存储，不释放工具组。
    如何服务大模型执行力：让 Skill 被选择后能找到对应工具集合。
    如何维持绝对边界：工具组仍以 ResourceRef 和 RelationRef 表达。
    """

    @abstractmethod
    def describe_tool_group_binding(
        self, request: ToolGroupBindingRequest, trace: TraceContext
    ) -> PortResult[ToolGroupBindingResponse]:
        """声明工具组绑定协议。"""
        raise NotImplementedError


class ToolDependencyPort(ABC):
    """工具依赖端口。

    中文名称：工具依赖端口。
    端口职责：定义工具间依赖、前置观察和关系引用协议。
    输入输出边界：输入 ToolDependencyRequest 与 TraceContext，输出 PortResult 包装的 ToolDependencyResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不执行依赖检查算法，不排序工具，不阻断真实流程。
    如何服务大模型执行力：让工具使用顺序和依赖可被说明。
    如何维持绝对边界：依赖事实以 L0 DependencyRef 表达。
    """

    @abstractmethod
    def describe_tool_dependency(self, request: ToolDependencyRequest, trace: TraceContext) -> PortResult[ToolDependencyResponse]:
        """声明工具依赖协议。"""
        raise NotImplementedError


class ToolUsageFlowPort(ABC):
    """工具使用流程端口。

    中文名称：工具使用流程端口。
    端口职责：定义工具调用顺序、可并行性和失败反馈协议。
    输入输出边界：输入 ToolUsageFlowRequest 与 TraceContext，输出 PortResult 包装的 ToolUsageFlowResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不执行流程，不调用工具，不生成真实计划。
    如何服务大模型执行力：把工具使用方式作为 Skill 流程的一部分说明给大模型。
    如何维持绝对边界：流程说明不触发任何真实动作。
    """

    @abstractmethod
    def describe_tool_usage_flow(self, request: ToolUsageFlowRequest, trace: TraceContext) -> PortResult[ToolUsageFlowResponse]:
        """声明工具使用流程协议。"""
        raise NotImplementedError
