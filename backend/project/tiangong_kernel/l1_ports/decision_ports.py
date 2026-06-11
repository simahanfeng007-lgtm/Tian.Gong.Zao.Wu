"""L1 决策边界端口协议。

本模块在 L1 中的职责：定义决策引用、决策记录、决策边界和决策反馈端口协议。
本模块定义：DecisionReferencePort、DecisionRecordPort、DecisionBoundaryPort、DecisionFeedbackPort。
本模块不实现：真实决策算法、真实权限裁决、真实审批流程、真实审计落盘或真实外部系统调用。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实权限系统、真实工具系统或真实模型系统。
本模块与 L2-L6 的关系：L2 可记录决策状态，L3 可引用决策反馈，L4 可实现真实适配，L5 可限制插件决策范围，L6 可提交子系统决策反馈。
本模块保证边界不是大模型执行障碍：只记录和反馈决策事实，不替大模型思考，也不替后续层做真实裁决。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.decision import Decision, DecisionRef
from tiangong_kernel.l0_primitives.effect import EffectRef
from tiangong_kernel.l0_primitives.event import EventRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import BoundaryHint, BoundaryRule, BoundaryViolation, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class DecisionBoundary:
    """决策边界对象。

    作用：表达 Decision 或 DecisionRef 的适用范围、策略边界和证据引用。
    边界：不执行裁决，不改变决策结果，不写外部审计库。
    """

    decision_ref: DecisionRef
    boundary: PortBoundary
    policy_ref: PolicyRef | None = None
    contract_ref: ContractRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionReferenceRequest:
    """决策引用请求。

    作用：声明调用方需要引用某个 DecisionRef 或 Decision 事实。
    边界：不做真实决策，不改变决策状态。
    """

    decision_ref: DecisionRef
    decision: Decision | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionReferenceResponse:
    """决策引用响应。

    作用：承载决策引用、可选决策事实和证据引用。
    边界：不代表已完成真实裁决，不代表可直接执行。
    """

    decision_ref: DecisionRef
    decision: Decision | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionRecordRequest:
    """决策记录请求。

    作用：声明需要记录的 Decision 事实、来源动作、事件和审计引用。
    边界：不落盘，不写审计库，不调用外部系统。
    """

    decision: Decision
    action_intent: ActionIntent | None = None
    command: CommandEnvelope | None = None
    event_ref: EventRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionRecordResponse:
    """决策记录响应。

    作用：承载决策引用、事件引用、审计引用和证据引用。
    边界：不代表真实记录已持久化，不触发通知。
    """

    decision_ref: DecisionRef
    event_ref: EventRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionBoundaryRequest:
    """决策边界请求。

    作用：声明需要说明某个决策事实适用范围的协议需求。
    边界：不执行裁决，不改变请求，不调用外部系统。
    """

    decision_ref: DecisionRef
    decision: Decision | None = None
    risk_view: RiskView | None = None
    policy_ref: PolicyRef | None = None
    resource_ref: ResourceRef | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionBoundaryResponse:
    """决策边界响应。

    作用：承载决策边界、规则和证据引用。
    边界：不代表允许继续，不代表已经拒绝。
    """

    boundary: DecisionBoundary
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionFeedbackRequest:
    """决策反馈请求。

    作用：声明后续层需要记录边界结果、越界事实、继续建议和更高层处理提示。
    边界：不实现反馈算法，不执行替代路径，不创建审批。
    """

    decision_ref: DecisionRef
    action_intent: ActionIntent | None = None
    boundary: DecisionBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    risk_view: RiskView | None = None
    effect_ref: EffectRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class DecisionFeedbackResponse:
    """决策反馈响应。

    作用：承载是否越界、是否建议继续、替代路径提示和验证引用。
    边界：不代表最终裁决，不执行反馈动作。
    """

    decision_ref: DecisionRef
    hint: BoundaryHint | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class DecisionReferencePort(ABC):
    """决策引用端口。

    中文名称：决策引用端口。
    端口职责：定义 DecisionRef 与 Decision 事实的引用协议。
    输入输出边界：输入 DecisionReferenceRequest 与 TraceContext，输出 PortResult 包装的 DecisionReferenceResponse。
    所属 L1 层：控制面决策端口协议。
    不承担的实现职责：不做真实决策，不改变决策事实，不触发执行。
    如何服务大模型执行力：让决策事实成为可引用对象，不把边界变成复杂审批链。
    如何维持绝对边界：决策引用携带范围和证据，不绕过边界。
    """

    @abstractmethod
    def reference_decision(
        self, request: DecisionReferenceRequest, trace: TraceContext
    ) -> PortResult[DecisionReferenceResponse]:
        """声明决策引用协议。"""
        raise NotImplementedError


class DecisionRecordPort(ABC):
    """决策记录端口。

    中文名称：决策记录端口。
    端口职责：定义 Decision 事实记录的协议。
    输入输出边界：输入 DecisionRecordRequest 与 TraceContext，输出 PortResult 包装的 DecisionRecordResponse。
    所属 L1 层：控制面决策端口协议。
    不承担的实现职责：不落盘，不写审计库，不调用外部系统。
    如何服务大模型执行力：为后续层保留事实链，不中断模型驱动的工作流。
    如何维持绝对边界：决策事实可追踪、可审计引用。
    """

    @abstractmethod
    def record_decision(self, request: DecisionRecordRequest, trace: TraceContext) -> PortResult[DecisionRecordResponse]:
        """声明决策记录协议。"""
        raise NotImplementedError


class DecisionBoundaryPort(ABC):
    """决策边界端口。

    中文名称：决策边界端口。
    端口职责：定义 Decision 对象适用范围的边界说明协议。
    输入输出边界：输入 DecisionBoundaryRequest 与 TraceContext，输出 PortResult 包装的 DecisionBoundaryResponse。
    所属 L1 层：控制面决策端口协议。
    不承担的实现职责：不执行裁决，不改变 Decision，不触发审批。
    如何服务大模型执行力：让后续层理解决策适用边界，避免误用。
    如何维持绝对边界：决策边界通过 PortBoundary 和规则表达。
    """

    @abstractmethod
    def describe_decision_boundary(
        self, request: DecisionBoundaryRequest, trace: TraceContext
    ) -> PortResult[DecisionBoundaryResponse]:
        """声明决策边界协议。"""
        raise NotImplementedError

    @abstractmethod
    def current_decision_boundary(self, trace: TraceContext) -> CoreResult[DecisionBoundary]:
        """声明当前决策边界读取协议。"""
        raise NotImplementedError


class DecisionFeedbackPort(ABC):
    """决策反馈端口。

    中文名称：决策反馈端口。
    端口职责：定义边界结果、越界事实、继续建议和替代路径的反馈协议。
    输入输出边界：输入 DecisionFeedbackRequest 与 TraceContext，输出 PortResult 包装的 DecisionFeedbackResponse。
    所属 L1 层：控制面决策端口协议。
    不承担的实现职责：不执行反馈算法，不创建审批，不调用工具。
    如何服务大模型执行力：将是否继续、是否替代、是否更高层处理的事实返回给编排层。
    如何维持绝对边界：反馈不覆盖边界事实，只引用边界事实。
    """

    @abstractmethod
    def submit_decision_feedback(
        self, request: DecisionFeedbackRequest, trace: TraceContext
    ) -> PortResult[DecisionFeedbackResponse]:
        """声明决策反馈协议。"""
        raise NotImplementedError
