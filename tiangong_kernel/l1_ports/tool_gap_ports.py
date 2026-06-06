"""L1 ToolGap 工具缺口端口协议。

本模块在 L1 中的职责：定义 Skill 缺口、工具需求、工具组缺口和工具边界缺口的报告协议。
本模块定义哪些端口：SkillGapReportPort、ToolNeedReportPort、ToolGroupGapReportPort、ToolGapBoundaryPort。
本模块不实现哪些能力：不生产工具、不注册工具、不修改工具组、不执行真实查询、不触发真实学习或迭代。
本模块禁止事项：不得访问文件、网络、数据库、插件目录、真实工具系统、真实模型系统或真实知识库。
本模块与 L2-L6 的关系：L2 可记录缺口状态，L3 可编排缺口处理候选，L4 可实现适配，L5 可限制插件缺口上报，L6 可由子系统报告缺口。
本模块如何服务“大模型先看 Skill，再释放工具组”：当 Skill 流程发现工具不足时，只把缺口表达为结构化报告，供后续阶段处理，不直接释放、生产或调用工具。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.relation import DependencyRef, RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class SkillGapReport:
    """Skill 缺口报告对象。

    作用：表达当前任务或目标下缺少合适 Skill、Skill 说明不足或 Skill 边界不清的结构化事实。
    边界：不生成 Skill，不修改知识库，不触发真实学习。
    """

    skill_ref: SkillRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    gap_signal_ref: SignalRef | None = None
    related_observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolNeedReport:
    """工具需求报告对象。

    作用：表达某个 Skill 或行动意图可能需要新工具、缺少工具或现有工具说明不足。
    边界：不生产工具，不注册工具，不改变工具组。
    """

    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    action_intent: ActionIntent | None = None
    need_signal_ref: SignalRef | None = None
    dependency_refs: tuple[DependencyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupGapReport:
    """工具组缺口报告对象。

    作用：表达某个 Skill 需要的工具集合、工具组关系或工具组可见视图存在缺口。
    边界：不创建工具组，不释放工具组，不扫描工具目录。
    """

    skill_ref: SkillRef | None = None
    tool_group_ref: ResourceRef | None = None
    relation_ref: RelationRef | None = None
    missing_tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolFunctionMismatchReport:
    """工具功能不匹配报告对象。

    作用：表达某个工具与 Skill 需要、输入输出边界或工具组关系不匹配的候选事实。
    边界：不修改工具，不生产工具，不调整工具组。
    """

    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    mismatch_signal_ref: SignalRef | None = None
    relation_ref: RelationRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGapBoundary:
    """工具缺口边界对象。

    作用：表达工具缺口报告适用的范围、策略引用、风险视图和边界事实。
    边界：只说明缺口边界，不做真实裁决，不生产工具。
    """

    skill_ref: SkillRef | None = None
    tool_ref: ToolRef | None = None
    tool_group_ref: ResourceRef | None = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillGapReportRequest:
    """Skill 缺口报告请求。作用：提交 Skill 缺口事实；边界：不生成 Skill。"""

    report: SkillGapReport
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class SkillGapReportResponse:
    """Skill 缺口报告响应。作用：返回 Skill 缺口报告和验证引用；边界：不代表真实采纳。"""

    report: SkillGapReport
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolNeedReportRequest:
    """工具需求报告请求。作用：提交工具需求或不足报告；边界：不生产工具。"""

    report: ToolNeedReport
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolNeedReportResponse:
    """工具需求报告响应。作用：返回工具需求报告和证据引用；边界：不注册工具。"""

    report: ToolNeedReport
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupGapReportRequest:
    """工具组缺口报告请求。作用：提交工具组关系或可见视图缺口；边界：不创建工具组。"""

    report: ToolGroupGapReport
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGroupGapReportResponse:
    """工具组缺口报告响应。作用：返回工具组缺口报告和验证引用；边界：不释放工具组。"""

    report: ToolGroupGapReport
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGapBoundaryRequest:
    """工具缺口边界请求。作用：声明需要说明的工具缺口边界；边界：不做真实裁决。"""

    boundary: ToolGapBoundary
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolGapBoundaryResponse:
    """工具缺口边界响应。作用：返回工具缺口边界和越界事实；边界：不阻断真实流程。"""

    boundary: ToolGapBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class SkillGapReportPort(ABC):
    """Skill 缺口报告端口。

    中文名称：Skill 缺口报告端口。
    端口职责：定义 Skill 缺口事实的提交协议。
    输入输出边界：输入 SkillGapReportRequest 与 TraceContext，输出 PortResult 包装的 SkillGapReportResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不生成 Skill，不写知识库，不执行学习。
    如何服务大模型执行力：让大模型发现没有合适 Skill 时能提交结构化缺口。
    如何维持绝对边界：缺口只作为候选证据，不直接改变系统。
    """

    @abstractmethod
    def submit_skill_gap_report(
        self, request: SkillGapReportRequest, trace: TraceContext
    ) -> PortResult[SkillGapReportResponse]:
        """声明 Skill 缺口报告协议。"""
        raise NotImplementedError


class ToolNeedReportPort(ABC):
    """工具需求报告端口。

    中文名称：工具需求报告端口。
    端口职责：定义 Skill 使用中工具不足或新工具需求的报告协议。
    输入输出边界：输入 ToolNeedReportRequest 与 TraceContext，输出 PortResult 包装的 ToolNeedReportResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不生产工具，不注册工具，不改工具组。
    如何服务大模型执行力：让模型可说明工具不足导致的执行卡点。
    如何维持绝对边界：需求报告不会触发真实工具生产链。
    """

    @abstractmethod
    def submit_tool_need_report(
        self, request: ToolNeedReportRequest, trace: TraceContext
    ) -> PortResult[ToolNeedReportResponse]:
        """声明工具需求报告协议。"""
        raise NotImplementedError


class ToolGroupGapReportPort(ABC):
    """工具组缺口报告端口。

    中文名称：工具组缺口报告端口。
    端口职责：定义工具组关系、组成和可见视图缺口报告协议。
    输入输出边界：输入 ToolGroupGapReportRequest 与 TraceContext，输出 PortResult 包装的 ToolGroupGapReportResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不创建工具组，不释放工具组，不扫描目录。
    如何服务大模型执行力：让模型可说明 Skill 所需工具集合不足。
    如何维持绝对边界：工具组缺口报告不等于工具组状态变更。
    """

    @abstractmethod
    def submit_tool_group_gap_report(
        self, request: ToolGroupGapReportRequest, trace: TraceContext
    ) -> PortResult[ToolGroupGapReportResponse]:
        """声明工具组缺口报告协议。"""
        raise NotImplementedError


class ToolGapBoundaryPort(ABC):
    """工具缺口边界端口。

    中文名称：工具缺口边界端口。
    端口职责：定义工具缺口报告适用范围和边界事实说明协议。
    输入输出边界：输入 ToolGapBoundaryRequest 与 TraceContext，输出 PortResult 包装的 ToolGapBoundaryResponse。
    所属 L1 层：Skill 直显与工具组端口协议的补丁扩展。
    不承担的实现职责：不做真实裁决，不触发审批，不生产工具。
    如何服务大模型执行力：让模型知道哪些缺口可以作为后续安全候选。
    如何维持绝对边界：边界只说明，不绕过控制面或验证链。
    """

    @abstractmethod
    def describe_tool_gap_boundary(
        self, request: ToolGapBoundaryRequest, trace: TraceContext
    ) -> PortResult[ToolGapBoundaryResponse]:
        """声明工具缺口边界说明协议。"""
        raise NotImplementedError
