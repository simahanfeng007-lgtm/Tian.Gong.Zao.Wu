"""L1 控制面边界端口协议。

本模块在 L1 中的职责：定义控制面边界检查、边界说明、替代路径、越界记录和工具组释放前边界检查端口。
本模块定义：BoundaryCheckPort、BoundaryExplainPort、BoundaryAlternativePort、BoundaryViolationRecordPort、ToolReleaseBoundaryPort。
本模块不实现：真实边界算法、真实裁决、真实风险评分、真实审批流程、真实工具释放或模型真实调用。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实权限系统、真实工具系统或真实模型系统。
本模块与 L2-L6 的关系：L2 可记录边界状态，L3 可调用轻量边界协议，L4 可实现外部适配，L5 可隔离插件越界，L6 可声明子系统边界。
本模块保证边界不是大模型执行障碍：只表达界限、原因和可替代路径，让后续层获得明确反馈，而不替大模型选择 Skill、选择工具或执行动作。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.decision import DecisionRef
from tiangong_kernel.l0_primitives.effect import EffectRef
from tiangong_kernel.l0_primitives.event import EventRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.metric import MetricRef
from tiangong_kernel.l0_primitives.namespace import NamespaceRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import TestRef, ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, PortBoundaryContext, QueryEnvelope
from .port_boundary import BoundaryHint, BoundaryRule, BoundaryViolation, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ControlBoundary:
    """控制面边界对象。

    作用：表达一次控制面边界可见范围、触碰规则、替代路径和证据引用。
    边界：只描述界限，不进行真实裁决、评分、审批或资源控制。
    """

    boundary: PortBoundary
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    contract_ref: ContractRef | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseBoundary:
    """工具组释放前边界对象。

    作用：表达 Skill 被选择后、工具组可见前需要检查的界限和引用。
    边界：不释放工具，不调用工具，不绑定真实工具句柄。
    """

    skill_ref: SkillRef
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    boundary: ControlBoundary | None = None
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryCheckRequest:
    """边界检查请求。

    作用：声明某个行动意图、目标、范围和边界上下文需要进行协议级检查。
    边界：不计算真实风险，不阻断大模型，不替大模型选择下一步。
    """

    action_intent: ActionIntent
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    resource_ref: ResourceRef | None = None
    risk_view: RiskView | None = None
    boundary_context: PortBoundaryContext | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryCheckResponse:
    """边界检查响应。

    作用：承载边界对象、越界事实、替代路径和验证引用。
    边界：不代表最终裁决，不触发审批，不执行任何替代动作。
    """

    boundary: ControlBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    decision_ref: DecisionRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryExplainRequest:
    """边界说明请求。

    作用：声明需要解释的边界、越界事实、行动意图与查询条件。
    边界：不生成真实解释算法，不调用模型，不改变执行路径。
    """

    boundary: ControlBoundary
    violation: BoundaryViolation | None = None
    action_intent: ActionIntent | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryExplainResponse:
    """边界说明响应。

    作用：承载边界提示、触碰规则、可替代路径和证据引用。
    边界：只表达可理解的说明事实，不做真实自然语言生成。
    """

    hint: BoundaryHint
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryAlternativeRequest:
    """边界替代路径请求。

    作用：声明当前行动意图触碰边界时需要哪些替代方向信息。
    边界：不拆分任务，不执行降级，不转入只读观察。
    """

    action_intent: ActionIntent
    boundary: ControlBoundary | None = None
    violation: BoundaryViolation | None = None
    observation_ref: ObservationRef | None = None
    signal_ref: SignalRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryAlternativeResponse:
    """边界替代路径响应。

    作用：承载可降级方向、可拆分方向、只读观察方向和后续处理提示。
    边界：不执行替代路径，不产生新计划，不调用工具。
    """

    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    downgraded_action_ref: EffectRef | None = None
    observation_ref: ObservationRef | None = None
    signal_ref: SignalRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryViolationRecordRequest:
    """越界记录请求。

    作用：声明需要记录的边界越界事实、来源事件、指标和证据引用。
    边界：不写日志，不落盘，不上报远程审计系统。
    """

    violation: BoundaryViolation
    boundary: ControlBoundary | None = None
    event_ref: EventRef | None = None
    metric_ref: MetricRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    namespace_ref: NamespaceRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BoundaryViolationRecordResponse:
    """越界记录响应。

    作用：承载越界记录后的事件、审计、指标和证据引用。
    边界：不代表真实持久化，不代表已经完成外部审计。
    """

    event_ref: EventRef | None = None
    audit_ref: AuditRef | None = None
    metric_ref: MetricRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseBoundaryRequest:
    """工具组释放前边界检查请求。

    作用：声明 Skill 选择后、工具组可见前的边界检查对象。
    边界：不释放工具，不调用工具，不替大模型选择 Skill 或工具。
    """

    skill_ref: SkillRef
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    action_intent: ActionIntent | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    risk_view: RiskView | None = None
    contract_ref: ContractRef | None = None
    test_ref: TestRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ToolReleaseBoundaryResponse:
    """工具组释放前边界检查响应。

    作用：承载工具组释放前需要关注的边界、越界事实与验证引用。
    边界：不释放工具，不创建工具租约，不执行任何工具动作。
    """

    boundary: ToolReleaseBoundary
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class BoundaryCheckPort(ABC):
    """边界检查端口。

    中文名称：边界检查端口。
    端口职责：定义请求是否可能触碰控制面边界的协议形式。
    输入输出边界：输入 BoundaryCheckRequest 与 TraceContext，输出 PortResult 包装的 BoundaryCheckResponse。
    所属 L1 层：控制面边界端口协议。
    不承担的实现职责：不实现真实边界算法，不做真实裁决，不选择 Skill 或工具。
    如何服务大模型执行力：通过结构化边界反馈让后续层明确可继续、可降级或需转向。
    如何维持绝对边界：把越界事实和证据以协议返回，保证界限可追踪。
    """

    @abstractmethod
    def check_boundary(self, request: BoundaryCheckRequest, trace: TraceContext) -> PortResult[BoundaryCheckResponse]:
        """声明边界检查协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_control_boundary(self, trace: TraceContext) -> CoreResult[ControlBoundary]:
        """声明控制面边界说明协议。"""
        raise NotImplementedError


class BoundaryExplainPort(ABC):
    """边界说明端口。

    中文名称：边界说明端口。
    端口职责：定义越界原因、触碰边界、替代路径和降级可能性的说明协议。
    输入输出边界：输入 BoundaryExplainRequest 与 TraceContext，输出 PortResult 包装的 BoundaryExplainResponse。
    所属 L1 层：控制面边界端口协议。
    不承担的实现职责：不生成真实解释算法，不调用模型，不改变控制流。
    如何服务大模型执行力：把阻塞式沉默改为可理解的原因和替代路径。
    如何维持绝对边界：说明被触碰的边界规则，避免模糊放行。
    """

    @abstractmethod
    def explain_boundary(self, request: BoundaryExplainRequest, trace: TraceContext) -> PortResult[BoundaryExplainResponse]:
        """声明边界说明协议。"""
        raise NotImplementedError


class BoundaryAlternativePort(ABC):
    """边界替代路径端口。

    中文名称：边界替代路径端口。
    端口职责：定义越界时的安全替代方向、降级方向和只读观察方向协议。
    输入输出边界：输入 BoundaryAlternativeRequest 与 TraceContext，输出 PortResult 包装的 BoundaryAlternativeResponse。
    所属 L1 层：控制面边界端口协议。
    不承担的实现职责：不执行替代动作，不拆解真实任务，不生成真实计划。
    如何服务大模型执行力：让后续层知道如何继续推进而不是停机。
    如何维持绝对边界：替代路径仍在声明边界内表达，不绕过边界。
    """

    @abstractmethod
    def propose_boundary_alternatives(
        self, request: BoundaryAlternativeRequest, trace: TraceContext
    ) -> PortResult[BoundaryAlternativeResponse]:
        """声明替代路径协议。"""
        raise NotImplementedError


class BoundaryViolationRecordPort(ABC):
    """越界记录端口。

    中文名称：越界记录端口。
    端口职责：定义越界事实、来源事件、指标和证据引用的记录协议。
    输入输出边界：输入 BoundaryViolationRecordRequest 与 TraceContext，输出 PortResult 包装的 BoundaryViolationRecordResponse。
    所属 L1 层：控制面边界端口协议。
    不承担的实现职责：不写日志，不落盘，不上报审计库。
    如何服务大模型执行力：为后续复盘提供事实引用，不中断正常协议链。
    如何维持绝对边界：把越界记录纳入可追踪事实链。
    """

    @abstractmethod
    def record_boundary_violation(
        self, request: BoundaryViolationRecordRequest, trace: TraceContext
    ) -> PortResult[BoundaryViolationRecordResponse]:
        """声明越界记录协议。"""
        raise NotImplementedError


class ToolReleaseBoundaryPort(ABC):
    """工具组释放前边界端口。

    中文名称：工具组释放前边界端口。
    端口职责：定义 Skill 被选择后、工具组可见前的边界检查协议。
    输入输出边界：输入 ToolReleaseBoundaryRequest 与 TraceContext，输出 PortResult 包装的 ToolReleaseBoundaryResponse。
    所属 L1 层：控制面边界端口协议。
    不承担的实现职责：不释放工具，不调用工具，不生成租约，不执行工具组。
    如何服务大模型执行力：让 Skill 到工具组的转换边界清晰而低摩擦。
    如何维持绝对边界：在工具组可见前保留可验证的边界事实。
    """

    @abstractmethod
    def check_tool_release_boundary(
        self, request: ToolReleaseBoundaryRequest, trace: TraceContext
    ) -> PortResult[ToolReleaseBoundaryResponse]:
        """声明工具组释放前边界检查协议。"""
        raise NotImplementedError
