"""L1 ToolGroup 工具组端口协议。

本模块在 L1 中的职责：定义工具组引用、工具组说明、工具组查询、工具组边界和工具组生命周期端口。
本模块定义哪些端口：ToolGroupReferencePort、ToolGroupDescriptionPort、ToolGroupQueryPort、ToolGroupBoundaryPort、ToolGroupLifecyclePort。
本模块不实现哪些能力：不实现真实工具组加载、真实工具释放、真实查询、真实生命周期处理或工具真实调用。
本模块禁止事项：不得扫描目录、访问数据库、连接网络、加载插件、占用真实资源或触发工具动作。
本模块与 L2-L6 的关系：L2 可记录工具组状态，L3 可编排 Skill 到工具组的协议链，L4 可实现真实适配，L5 可隔离插件工具组，L6 可声明子系统工具组。
本模块如何服务“大模型先看 Skill，再释放工具组”：工具组作为 Skill 被选择后的工具集合引用存在，只描述可见工具集合，不替代 Skill，也不暴露内部端口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult


class ToolGroupLifecycleState(str, Enum):
    """工具组生命周期状态枚举；只表达协议状态，不处理真实释放、撤销或过期。"""

    DECLARED = "declared"
    VISIBLE = "visible"
    RELEASED = "released"
    REVOKED = "revoked"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ToolGroupBoundary:
    """工具组边界对象。

    作用：表达工具组适用 Skill、可见范围、策略引用和风险边界。
    边界：只说明工具组界限，不做真实裁决，不加载工具，不释放工具。
    """

    tool_group_ref: ResourceRef
    skill_ref: SkillRef | None = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    contract_ref: ContractRef | None = None
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupView:
    """工具组视图。

    作用：表达工具组包含的工具引用、适用 Skill、边界和关系引用。
    边界：不加载工具，不暴露真实实现，不作为历史封装执行计划。
    """

    tool_group_ref: ResourceRef
    skill_ref: SkillRef | None = None
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    relation_ref: RelationRef | None = None
    boundary: ToolGroupBoundary | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupReferenceRequest:
    """工具组引用请求。作用：声明需要引用的工具组资源；边界：不占用真实资源。"""

    tool_group_ref: ResourceRef
    namespace_ref: NamespaceRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupReferenceResponse:
    """工具组引用响应。作用：返回工具组引用、版本和证据；边界：不代表工具组已释放。"""

    tool_group_ref: ResourceRef
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupDescriptionRequest:
    """工具组说明请求。作用：声明需要说明的工具组；边界：不加载工具。"""

    tool_group_ref: ResourceRef
    skill_ref: SkillRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupDescriptionResponse:
    """工具组说明响应。作用：承载工具组视图；边界：不包含真实工具入口。"""

    view: ToolGroupView
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupQueryRequest:
    """工具组查询请求。作用：声明按 Skill 或范围查询工具组引用；边界：不实现真实查询。"""

    query: QueryEnvelope
    skill_ref: SkillRef | None = None
    scope_ref: ScopeRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupQueryResponse:
    """工具组查询响应。作用：承载候选工具组引用；边界：不代表真实排序或真实可用性。"""

    tool_group_refs: tuple[ResourceRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupBoundaryRequest:
    """工具组边界请求。作用：声明需要说明的工具组使用边界；边界：不做真实裁决。"""

    tool_group_ref: ResourceRef
    skill_ref: SkillRef | None = None
    risk_view: RiskView | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupBoundaryResponse:
    """工具组边界响应。作用：承载工具组边界和越界事实；边界：不释放工具。"""

    boundary: ToolGroupBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupLifecycleRequest:
    """工具组生命周期请求。作用：声明工具组生命周期状态事实；边界：不执行释放、撤销或过期处理。"""

    tool_group_ref: ResourceRef
    state: ToolGroupLifecycleState = ToolGroupLifecycleState.UNKNOWN
    skill_ref: SkillRef | None = None
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupLifecycleResponse:
    """工具组生命周期响应。作用：返回工具组状态事实和验证引用；边界：不改变真实状态。"""

    tool_group_ref: ResourceRef
    state: ToolGroupLifecycleState = ToolGroupLifecycleState.UNKNOWN
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ToolGroupReferencePort(ABC):
    """工具组引用端口。

    中文名称：工具组引用端口。
    端口职责：定义工具组资源引用协议。
    输入输出边界：输入 ToolGroupReferenceRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupReferenceResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不创建工具组，不占用真实资源。
    如何服务大模型执行力：为 Skill 到工具集合的转换提供稳定引用。
    如何维持绝对边界：工具组以 ResourceRef 表达，不新造身份体系。
    """

    @abstractmethod
    def reference_tool_group(self, request: ToolGroupReferenceRequest, trace: TraceContext) -> PortResult[ToolGroupReferenceResponse]:
        """声明工具组引用协议。"""
        raise NotImplementedError


class ToolGroupDescriptionPort(ABC):
    """工具组说明端口。

    中文名称：工具组说明端口。
    端口职责：定义工具组包含哪些工具、适用哪个 Skill、输入输出边界的说明协议。
    输入输出边界：输入 ToolGroupDescriptionRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupDescriptionResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不加载工具，不暴露真实实现。
    如何服务大模型执行力：让大模型在 Skill 流程中理解可用工具集合。
    如何维持绝对边界：只说明可见工具引用和边界。
    """

    @abstractmethod
    def describe_tool_group(self, request: ToolGroupDescriptionRequest, trace: TraceContext) -> PortResult[ToolGroupDescriptionResponse]:
        """声明工具组说明协议。"""
        raise NotImplementedError


class ToolGroupQueryPort(ABC):
    """工具组查询端口。

    中文名称：工具组查询端口。
    端口职责：定义按 Skill 或范围查询工具组引用的协议。
    输入输出边界：输入 ToolGroupQueryRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupQueryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不扫描文件，不访问数据库，不实现排序。
    如何服务大模型执行力：为 Skill 选择后定位工具组提供协议形状。
    如何维持绝对边界：查询结果仍是引用，不产生释放动作。
    """

    @abstractmethod
    def query_tool_groups(self, request: ToolGroupQueryRequest, trace: TraceContext) -> PortResult[ToolGroupQueryResponse]:
        """声明工具组查询协议。"""
        raise NotImplementedError


class ToolGroupBoundaryPort(ABC):
    """工具组边界端口。

    中文名称：工具组边界端口。
    端口职责：定义工具组适用范围和风险边界说明协议。
    输入输出边界：输入 ToolGroupBoundaryRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupBoundaryResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不做真实裁决，不释放工具。
    如何服务大模型执行力：让工具组边界可被大模型和后续层理解。
    如何维持绝对边界：越界事实显式返回，不绕过控制面。
    """

    @abstractmethod
    def describe_tool_group_boundary(
        self, request: ToolGroupBoundaryRequest, trace: TraceContext
    ) -> PortResult[ToolGroupBoundaryResponse]:
        """声明工具组边界协议。"""
        raise NotImplementedError


class ToolGroupLifecyclePort(ABC):
    """工具组生命周期端口。

    中文名称：工具组生命周期端口。
    端口职责：定义 declared、visible、released、revoked、expired 等状态事实协议。
    输入输出边界：输入 ToolGroupLifecycleRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupLifecycleResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不实现真实释放、撤销、过期或资源清理。
    如何服务大模型执行力：让大模型可理解工具组是否处在可见链路中。
    如何维持绝对边界：生命周期只表达事实状态，不改变真实系统。
    """

    @abstractmethod
    def describe_tool_group_lifecycle(
        self, request: ToolGroupLifecycleRequest, trace: TraceContext
    ) -> PortResult[ToolGroupLifecycleResponse]:
        """声明工具组生命周期协议。"""
        raise NotImplementedError
