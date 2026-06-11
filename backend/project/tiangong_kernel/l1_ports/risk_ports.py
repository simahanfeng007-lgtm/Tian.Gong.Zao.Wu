"""L1 风险边界端口协议。

本模块在 L1 中的职责：定义风险视图、风险边界、风险说明和风险升级提示端口协议。
本模块定义：RiskViewPort、RiskBoundaryPort、RiskExplainPort、RiskEscalationHintPort。
本模块不实现：真实风险评分、真实 A 等级算法、真实权限裁决、真实确认票据或真实授权租约。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实权限系统、真实工具系统或真实模型系统。
本模块与 L2-L6 的关系：L2 可记录风险状态，L3 可引用风险边界，L4 可实现真实风险适配，L5 可隔离插件风险范围，L6 可提交子系统风险视图。
本模块保证边界不是大模型执行障碍：只表达风险视图和升级提示，不让大模型每一步进入审批等待。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent
from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskRef, RiskView
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import QueryEnvelope
from .port_boundary import BoundaryHint, BoundaryRule, PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class RiskBoundary:
    """风险边界对象。

    作用：表达风险视图、边界说明、适用范围和证据引用。
    边界：不计算风险，不阻断动作，不生成确认票据。
    """

    risk_view: RiskView
    boundary: PortBoundary
    scope_ref: ScopeRef | None = None
    policy_ref: PolicyRef | None = None
    contract_ref: ContractRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskViewSubmitRequest:
    """风险视图提交请求。

    作用：声明已有 RiskView 需要进入 L1 控制面边界协议。
    边界：不计算风险分数，不改变风险等级，不裁决。
    """

    risk_view: RiskView
    action_intent: ActionIntent | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    observation_ref: ObservationRef | None = None
    signal_ref: SignalRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskViewSubmitResponse:
    """风险视图提交响应。

    作用：承载被接受的风险引用和验证引用。
    边界：不代表真实风险系统已保存，不代表已完成裁决。
    """

    risk_ref: RiskRef
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskViewReadRequest:
    """风险视图读取请求。

    作用：声明按 RiskRef 或查询信封读取风险视图的协议需求。
    边界：不查询真实数据库，不读取文件，不调用风险引擎。
    """

    risk_ref: RiskRef
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskViewReadResponse:
    """风险视图读取响应。

    作用：承载风险引用和可选风险视图事实。
    边界：不代表真实风险库读取，不进行评分转换。
    """

    risk_ref: RiskRef
    risk_view: RiskView | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskBoundaryRequest:
    """风险边界请求。

    作用：声明某个风险视图、动作和资源可能触及的风险边界。
    边界：不阻断，不裁决，不升级真实权限。
    """

    risk_view: RiskView
    action_intent: ActionIntent | None = None
    resource_ref: ResourceRef | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    query: QueryEnvelope | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskBoundaryResponse:
    """风险边界响应。

    作用：承载风险边界、规则和证据引用。
    边界：不代表允许或拒绝，只说明风险界限。
    """

    boundary: RiskBoundary
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskExplainRequest:
    """风险说明请求。

    作用：声明需要说明的风险视图、边界和查询条件。
    边界：不调用模型，不生成真实解释，不改变风险级别。
    """

    risk_view: RiskView
    boundary: RiskBoundary | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskExplainResponse:
    """风险说明响应。

    作用：承载风险提示、规则、验证和证据引用。
    边界：只表达说明事实，不做解释算法。
    """

    hint: BoundaryHint
    risk_ref: RiskRef
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskEscalationHintRequest:
    """风险升级提示请求。

    作用：声明某个风险视图可能需要更高层边界处理。
    边界：不生成确认票据，不生成授权租约，不进入审批流。
    """

    risk_view: RiskView
    action_intent: ActionIntent | None = None
    boundary: RiskBoundary | None = None
    signal_ref: SignalRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RiskEscalationHintResponse:
    """风险升级提示响应。

    作用：承载升级提示、可处理范围、验证和证据引用。
    边界：不代表已经升级，不要求每一步审批。
    """

    hint: BoundaryHint
    risk_ref: RiskRef
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class RiskViewPort(ABC):
    """风险视图端口。

    中文名称：风险视图端口。
    端口职责：定义 RiskView 的提交、读取和转换边界协议。
    输入输出边界：输入风险视图请求与 TraceContext，输出 PortResult 包装的响应对象。
    所属 L1 层：控制面风险端口协议。
    不承担的实现职责：不评分，不实现 A 等级算法，不做最终裁决。
    如何服务大模型执行力：把风险作为可引用事实提供，而不是隐藏式拦截。
    如何维持绝对边界：风险事实通过 RiskView 和证据引用保持可追踪。
    """

    @abstractmethod
    def submit_risk_view(self, request: RiskViewSubmitRequest, trace: TraceContext) -> PortResult[RiskViewSubmitResponse]:
        """声明风险视图提交协议。"""
        raise NotImplementedError

    @abstractmethod
    def read_risk_view(self, request: RiskViewReadRequest, trace: TraceContext) -> PortResult[RiskViewReadResponse]:
        """声明风险视图读取协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_risk_view_boundary(self, trace: TraceContext) -> CoreResult[RiskBoundary]:
        """声明风险视图边界说明协议。"""
        raise NotImplementedError


class RiskBoundaryPort(ABC):
    """风险边界端口。

    中文名称：风险边界端口。
    端口职责：定义请求可能触及的风险边界说明协议。
    输入输出边界：输入 RiskBoundaryRequest 与 TraceContext，输出 PortResult 包装的 RiskBoundaryResponse。
    所属 L1 层：控制面风险端口协议。
    不承担的实现职责：不阻断，不执行，不生成审批。
    如何服务大模型执行力：提前暴露风险界限，支持后续层连续推进。
    如何维持绝对边界：风险边界始终以 PortBoundary 形式返回。
    """

    @abstractmethod
    def describe_risk_boundary(self, request: RiskBoundaryRequest, trace: TraceContext) -> PortResult[RiskBoundaryResponse]:
        """声明风险边界协议。"""
        raise NotImplementedError


class RiskExplainPort(ABC):
    """风险说明端口。

    中文名称：风险说明端口。
    端口职责：定义风险说明材料、提示和规则返回协议。
    输入输出边界：输入 RiskExplainRequest 与 TraceContext，输出 PortResult 包装的 RiskExplainResponse。
    所属 L1 层：控制面风险端口协议。
    不承担的实现职责：不调用模型，不生成真实解释，不改变风险事实。
    如何服务大模型执行力：让风险边界可理解，减少无效重试。
    如何维持绝对边界：说明不改变风险边界本身。
    """

    @abstractmethod
    def explain_risk(self, request: RiskExplainRequest, trace: TraceContext) -> PortResult[RiskExplainResponse]:
        """声明风险说明协议。"""
        raise NotImplementedError


class RiskEscalationHintPort(ABC):
    """风险升级提示端口。

    中文名称：风险升级提示端口。
    端口职责：定义可能需要更高层处理的风险提示协议。
    输入输出边界：输入 RiskEscalationHintRequest 与 TraceContext，输出 PortResult 包装的 RiskEscalationHintResponse。
    所属 L1 层：控制面风险端口协议。
    不承担的实现职责：不生成确认票据，不生成授权租约，不创建审批流。
    如何服务大模型执行力：只提示可能升级，避免把每一步变成审批等待。
    如何维持绝对边界：高边界处理需求以显式提示返回。
    """

    @abstractmethod
    def hint_risk_escalation(
        self, request: RiskEscalationHintRequest, trace: TraceContext
    ) -> PortResult[RiskEscalationHintResponse]:
        """声明风险升级提示协议。"""
        raise NotImplementedError
