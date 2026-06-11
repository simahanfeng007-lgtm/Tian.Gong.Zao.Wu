"""L1 ToolRelease 工具组释放协议端口。

本模块在 L1 中的职责：定义工具组释放意图、释放请求、释放结果、释放后可见视图和撤销协议。
本模块定义哪些端口：ToolReleaseIntentPort、ToolReleaseRequestPort、ToolReleaseResultPort、ToolReleaseViewPort、ToolReleaseRevocationPort。
本模块不实现哪些能力：不实现真实工具释放、工具真实调用、真实租约生成、真实撤销、真实资源清理或模型真实调用。
本模块禁止事项：不得连接工具系统、不得修改全局状态、不得关闭资源、不得生成真实授权、不得访问文件网络数据库。
本模块与 L2-L6 的关系：L2 可记录释放视图状态，L3 可编排 Skill 到工具组的转换，L4 可实现真实工具适配，L5 可限制插件工具可见性，L6 可声明子系统工具组需求。
本模块如何服务“大模型先看 Skill，再释放工具组”：只定义 Skill 选中后工具组从意图到可见视图的协议结构，不直接暴露内部端口，不进行真实释放。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.decision import DecisionRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.metric import MetricRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
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

from .control_boundary_ports import ToolReleaseBoundary
from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ToolReleaseView:
    """工具组释放后可见视图。

    作用：表达 Skill 所需工具组在大模型侧可见的工具引用、边界、关系和证据。
    边界：不暴露内部端口，不暴露真实工具实现，不包含真实资源句柄。
    """

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    visible_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    boundary: ToolReleaseBoundary | None = None
    relation_ref: RelationRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseIntentRequest:
    """工具组释放意图请求。

    作用：表达某个 Skill 被选择后可能需要释放某个工具组的意图。
    边界：不释放工具，不生成租约，不改变全局状态。
    """

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    action_intent: ActionIntent | None = None
    scope_ref: ScopeRef | None = None
    risk_view: RiskView | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseIntentResponse:
    """工具组释放意图响应。作用：承载意图信号和边界引用；边界：不代表已经释放。"""

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    signal_ref: SignalRef | None = None
    boundary: ToolReleaseBoundary | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseRequest:
    """工具组释放请求。

    作用：定义释放请求结构，包含 Skill、工具组、候选工具和命令信封。
    边界：不调用工具系统，不生成真实授权，不改变全局状态。
    """

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    requested_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    command: CommandEnvelope | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    contract_ref: ContractRef | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseResponse:
    """工具组释放响应。作用：承载释放协议视图、越界事实和验证引用；边界：不代表真实释放完成。"""

    view: ToolReleaseView | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    decision_ref: DecisionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseResultRequest:
    """工具组释放结果请求。作用：声明需要表达的释放结果引用；边界：不产生真实结果。"""

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    query: QueryEnvelope | None = None
    observation_ref: ObservationRef | None = None
    metric_ref: MetricRef | None = None
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseResultResponse:
    """工具组释放结果响应。作用：承载释放视图、观察、指标和审计引用；边界：不代表真实工具可用。"""

    view: ToolReleaseView | None = None
    observation_ref: ObservationRef | None = None
    metric_ref: MetricRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseViewRequest:
    """工具组释放视图请求。作用：声明需要给大模型可见的工具组视图；边界：不暴露内部端口。"""

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    query: QueryEnvelope | None = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseViewResponse:
    """工具组释放视图响应。作用：承载大模型可见的工具组视图；边界：不暴露敏感实现。"""

    view: ToolReleaseView
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseRevocationRequest:
    """工具组撤销请求。作用：声明工具组撤销协议事实；边界：不关闭资源、不清理真实工具。"""

    skill_ref: SkillRef
    tool_group_ref: ResourceRef
    visible_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    reason_signal_ref: SignalRef | None = None
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseRevocationResponse:
    """工具组撤销响应。作用：承载撤销信号、审计引用和证据；边界：不代表真实撤销完成。"""

    signal_ref: SignalRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ToolReleaseIntentPort(ABC):
    """工具组释放意图端口。

    中文名称：工具组释放意图端口。
    端口职责：定义 Skill 被选择后可能需要释放某个工具组的意图协议。
    输入输出边界：输入 ToolReleaseIntentRequest 与 TraceContext，输出 PortResult 包装的 ToolReleaseIntentResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不释放工具，不生成真实授权，不改状态。
    如何服务大模型执行力：让 Skill 到工具组的转换先有明确意图。
    如何维持绝对边界：意图只以引用和边界上下文表达。
    """

    @abstractmethod
    def declare_tool_release_intent(
        self, request: ToolReleaseIntentRequest, trace: TraceContext
    ) -> PortResult[ToolReleaseIntentResponse]:
        """声明工具组释放意图协议。"""
        raise NotImplementedError


class ToolReleaseRequestPort(ABC):
    """工具组释放请求端口。

    中文名称：工具组释放请求端口。
    端口职责：定义释放请求结构和协议返回。
    输入输出边界：输入 ToolReleaseRequest 与 TraceContext，输出 PortResult 包装的 ToolReleaseResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不调用工具系统，不生成租约，不触发真实释放。
    如何服务大模型执行力：让后续层在边界清楚时构造工具组可见链路。
    如何维持绝对边界：请求仍需携带边界上下文、策略和合约引用。
    """

    @abstractmethod
    def request_tool_release(self, request: ToolReleaseRequest, trace: TraceContext) -> PortResult[ToolReleaseResponse]:
        """声明工具组释放请求协议。"""
        raise NotImplementedError


class ToolReleaseResultPort(ABC):
    """工具组释放结果端口。

    中文名称：工具组释放结果端口。
    端口职责：定义释放结果的观察、指标、审计和视图返回协议。
    输入输出边界：输入 ToolReleaseResultRequest 与 TraceContext，输出 PortResult 包装的 ToolReleaseResultResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不产生真实结果，不确认真实工具可用。
    如何服务大模型执行力：让大模型获得结构化可见工具组结果。
    如何维持绝对边界：结果只以引用和视图表达。
    """

    @abstractmethod
    def describe_tool_release_result(
        self, request: ToolReleaseResultRequest, trace: TraceContext
    ) -> PortResult[ToolReleaseResultResponse]:
        """声明工具组释放结果协议。"""
        raise NotImplementedError


class ToolReleaseViewPort(ABC):
    """工具组释放视图端口。

    中文名称：工具组释放视图端口。
    端口职责：定义释放后大模型可见的工具组视图协议。
    输入输出边界：输入 ToolReleaseViewRequest 与 TraceContext，输出 PortResult 包装的 ToolReleaseViewResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不暴露内部端口，不暴露敏感实现，不调用模型。
    如何服务大模型执行力：让大模型看到 Skill 所需工具组而不是底层端口。
    如何维持绝对边界：可见视图只包含引用、边界和证据。
    """

    @abstractmethod
    def describe_tool_release_view(
        self, request: ToolReleaseViewRequest, trace: TraceContext
    ) -> PortResult[ToolReleaseViewResponse]:
        """声明工具组释放视图协议。"""
        raise NotImplementedError


class ToolReleaseRevocationPort(ABC):
    """工具组撤销端口。

    中文名称：工具组撤销端口。
    端口职责：定义工具组撤销请求与撤销结果引用协议。
    输入输出边界：输入 ToolReleaseRevocationRequest 与 TraceContext，输出 PortResult 包装的 ToolReleaseRevocationResponse。
    所属 L1 层：Skill 直显与工具组端口协议。
    不承担的实现职责：不执行撤销，不关闭资源，不清理真实工具。
    如何服务大模型执行力：让工具组可见范围可以被后续层声明收回。
    如何维持绝对边界：撤销只记录协议事实，不直接操作真实系统。
    """

    @abstractmethod
    def revoke_tool_release(
        self, request: ToolReleaseRevocationRequest, trace: TraceContext
    ) -> PortResult[ToolReleaseRevocationResponse]:
        """声明工具组撤销协议。"""
        raise NotImplementedError
