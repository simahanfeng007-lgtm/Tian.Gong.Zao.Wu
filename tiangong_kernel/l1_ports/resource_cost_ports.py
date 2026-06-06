"""L1 资源用量与成本记录端口声明。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class ResourceUsageReportRequest:
    """资源用量报告请求，承载用量、预算、配额和限流引用。"""

    request_ref: TypedRef
    usage_report_ref: TypedRef
    budget_ref: TypedRef | None = None
    quota_ref: TypedRef | None = None
    rate_limit_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ResourceUsageReportResponse:
    """资源用量报告响应，返回用量和实际成本引用。"""

    response_ref: TypedRef
    usage_report_ref: TypedRef
    cost_actual_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CostRecordRequest:
    """成本记录请求，承载预估成本、实际成本和审计要求引用。"""

    request_ref: TypedRef
    cost_estimate_ref: TypedRef | None = None
    cost_actual_ref: TypedRef | None = None
    audit_required_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class CostRecordResponse:
    """成本记录响应，返回成本记录引用。"""

    response_ref: TypedRef
    cost_record_ref: TypedRef
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BudgetExpansionReviewRequest:
    """预算扩展复核请求，声明上限、有效期、理由和高权限引用。"""

    request_ref: TypedRef
    requested_extra_budget_ref: TypedRef
    upper_bound_ref: TypedRef
    valid_until_ref: TypedRef
    reason_ref: TypedRef
    audit_required_ref: TypedRef
    high_permission_ref: TypedRef | None = None
    unlimited: bool = False
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class BudgetExpansionReviewResponse:
    """预算扩展复核响应，返回复核、批准或拒绝引用。"""

    response_ref: TypedRef
    review_ref: TypedRef
    approved_ref: TypedRef | None = None
    rejected_ref: TypedRef | None = None
    schema_version: str = "0.1"


class ResourceUsageReportPort(ABC):
    """资源用量报告端口，不执行资源扣减。"""

    @abstractmethod
    def report_resource_usage(self, request: ResourceUsageReportRequest, trace: TraceContext) -> PortResult[ResourceUsageReportResponse]:
        raise NotImplementedError


class CostRecordPort(ABC):
    """成本记录端口，不落地真实账务记录。"""

    @abstractmethod
    def record_cost(self, request: CostRecordRequest, trace: TraceContext) -> PortResult[CostRecordResponse]:
        raise NotImplementedError


class BudgetExpansionReviewPort(ABC):
    """预算扩展复核端口，只声明复核边界。"""

    @abstractmethod
    def review_budget_expansion(self, request: BudgetExpansionReviewRequest, trace: TraceContext) -> PortResult[BudgetExpansionReviewResponse]:
        raise NotImplementedError
