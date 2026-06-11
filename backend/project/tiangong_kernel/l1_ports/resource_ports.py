"""L1 资源端口协议。

本模块在 L1 中的职责：定义资源、预算、配额、速率限制与资源预约端口协议。
本模块定义：ResourcePort、BudgetPort、QuotaPort、RateLimitPort、ResourceReservationPort。
本模块不实现：真实资源占用、真实预算计算、真实限流、真实排队或真实资源锁定。
本模块禁止事项：不得访问文件、网络、数据库、后台任务、真实环境、模型或工具。
本模块与 L2-L6 的关系：L2 可记录资源状态，L3 可组织资源预算边界，L4 可实现外部资源适配，L5 可隔离插件资源预算，L6 可提交子系统资源请求事实。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.cost_budget import BudgetRef, QuotaRef, RateLimitRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .envelope import CommandEnvelope, QueryEnvelope
from .port_boundary import PortBoundary
from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ResourcePortBoundary:
    """资源端口边界对象。

    作用：表达资源、预算、配额、速率限制与预约的协议边界。
    边界：只描述资源界限，不占用、不锁定、不计算真实资源。
    """

    boundary: PortBoundary
    resource_ref: ResourceRef | None = None
    budget_ref: BudgetRef | None = None
    quota_ref: QuotaRef | None = None
    rate_limit_ref: RateLimitRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ResourceDeclareRequest:
    """资源声明请求。

    作用：声明资源引用、范围与结构版本之间的协议关系。
    边界：不打开资源，不占用资源，不访问真实系统。
    """

    resource_ref: ResourceRef
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_ref: SchemaRef | None = None
    version_ref: VersionRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ResourceDeclareResponse:
    """资源声明响应。

    作用：承载被声明的资源引用、范围引用与审计引用。
    边界：不代表资源可用，不代表资源已占用。
    """

    resource_ref: ResourceRef
    scope_ref: ScopeRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BudgetCheckRequest:
    """预算检查请求。

    作用：声明需要检查的预算引用、资源引用或查询边界。
    边界：不计算真实预算，不扣减额度，不记录消费。
    """

    budget_ref: BudgetRef
    resource_ref: ResourceRef | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BudgetCheckResponse:
    """预算检查响应。

    作用：承载预算引用、资源引用和验证引用。
    边界：不返回裸数值，不代表真实额度已经核算。
    """

    budget_ref: BudgetRef
    resource_ref: ResourceRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class QuotaCheckRequest:
    """配额检查请求。

    作用：声明需要检查的配额引用、资源引用与范围。
    边界：不连接真实限额系统，不扣减配额，不阻塞调用。
    """

    quota_ref: QuotaRef
    resource_ref: ResourceRef | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class QuotaCheckResponse:
    """配额检查响应。

    作用：承载配额引用、资源引用和验证引用。
    边界：不返回裸数值，不执行真实限额裁决。
    """

    quota_ref: QuotaRef
    resource_ref: ResourceRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RateLimitCheckRequest:
    """速率限制检查请求。

    作用：声明需要检查的速率限制引用、资源引用与范围。
    边界：不实现真实限流器，不等待，不排队，不调度。
    """

    rate_limit_ref: RateLimitRef
    resource_ref: ResourceRef | None = None
    query: QueryEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class RateLimitCheckResponse:
    """速率限制检查响应。

    作用：承载速率限制引用、资源引用和验证引用。
    边界：不代表真实队列状态，不产生等待或重试行为。
    """

    rate_limit_ref: RateLimitRef
    resource_ref: ResourceRef | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ResourceReservationRequest:
    """资源预约请求。

    作用：声明资源、预算、配额和速率限制之间的预约意图。
    边界：不锁定真实资源，不占用额度，不创建排队任务。
    """

    resource_ref: ResourceRef
    budget_ref: BudgetRef | None = None
    quota_ref: QuotaRef | None = None
    rate_limit_ref: RateLimitRef | None = None
    command: CommandEnvelope | None = None
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ResourceReservationResponse:
    """资源预约响应。

    作用：承载预约意图被接受后的资源、预算、配额和审计引用。
    边界：不代表真实资源已锁定，不保证后续执行可用。
    """

    resource_ref: ResourceRef
    budget_ref: BudgetRef | None = None
    quota_ref: QuotaRef | None = None
    rate_limit_ref: RateLimitRef | None = None
    audit_ref: AuditRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class ResourcePort(ABC):
    """资源端口。

    中文名称：资源声明端口。
    端口职责：定义资源引用、资源声明与资源边界的 L1 协议。
    输入输出边界：输入 ResourceDeclareRequest 与 TraceContext，输出 PortResult 包装的 ResourceDeclareResponse。
    所属 L1 层：资源端口协议。
    不承担的实现职责：不占用真实资源，不连接外部资源系统。
    """

    @abstractmethod
    def declare_resource(self, request: ResourceDeclareRequest, trace: TraceContext) -> PortResult[ResourceDeclareResponse]:
        """声明资源引用协议。"""
        raise NotImplementedError

    @abstractmethod
    def describe_resource_boundary(self, trace: TraceContext) -> CoreResult[ResourcePortBoundary]:
        """声明资源边界说明协议。"""
        raise NotImplementedError


class BudgetPort(ABC):
    """预算端口。

    中文名称：预算检查端口。
    端口职责：定义预算声明和预算检查的 L1 协议。
    输入输出边界：输入 BudgetCheckRequest 与 TraceContext，输出 PortResult 包装的 BudgetCheckResponse。
    所属 L1 层：资源端口协议。
    不承担的实现职责：不计算真实预算，不扣减额度，不做费用结算。
    """

    @abstractmethod
    def check_budget(self, request: BudgetCheckRequest, trace: TraceContext) -> PortResult[BudgetCheckResponse]:
        """声明预算检查协议。"""
        raise NotImplementedError


class QuotaPort(ABC):
    """配额端口。

    中文名称：配额边界端口。
    端口职责：定义配额引用和配额边界的 L1 协议。
    输入输出边界：输入 QuotaCheckRequest 与 TraceContext，输出 PortResult 包装的 QuotaCheckResponse。
    所属 L1 层：资源端口协议。
    不承担的实现职责：不连接真实限额系统，不扣减配额。
    """

    @abstractmethod
    def check_quota(self, request: QuotaCheckRequest, trace: TraceContext) -> PortResult[QuotaCheckResponse]:
        """声明配额检查协议。"""
        raise NotImplementedError


class RateLimitPort(ABC):
    """速率限制端口。

    中文名称：速率限制协议端口。
    端口职责：定义速率限制引用和检查边界的 L1 协议。
    输入输出边界：输入 RateLimitCheckRequest 与 TraceContext，输出 PortResult 包装的 RateLimitCheckResponse。
    所属 L1 层：资源端口协议。
    不承担的实现职责：不实现真实限流器，不等待，不排队。
    """

    @abstractmethod
    def check_rate_limit(
        self, request: RateLimitCheckRequest, trace: TraceContext
    ) -> PortResult[RateLimitCheckResponse]:
        """声明速率限制检查协议。"""
        raise NotImplementedError


class ResourceReservationPort(ABC):
    """资源预约端口。

    中文名称：资源预约端口。
    端口职责：定义资源预约请求的 L1 协议。
    输入输出边界：输入 ResourceReservationRequest 与 TraceContext，输出 PortResult 包装的 ResourceReservationResponse。
    所属 L1 层：资源端口协议。
    不承担的实现职责：不锁定真实资源，不占用额度，不创建排队任务。
    """

    @abstractmethod
    def reserve_resource(
        self, request: ResourceReservationRequest, trace: TraceContext
    ) -> PortResult[ResourceReservationResponse]:
        """声明资源预约协议。"""
        raise NotImplementedError
