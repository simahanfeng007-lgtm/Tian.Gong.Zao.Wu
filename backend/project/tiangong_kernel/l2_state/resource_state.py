"""L2 资源状态对象。

作用：记录外部给出的预算、配额、限速、租约和资源压力状态事实。
边界：不读取真实资源，不扣减预算，不等待限速，不创建、续租或撤销租约。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ResourceStatus(str, Enum):
    """资源状态。

    作用：表达外部系统记录的可用、受限、已预留、已使用、耗尽或限速状态。
    边界：不计量资源，不扣减预算，不重试或等待。
    """

    UNKNOWN = "unknown"
    AVAILABLE = "available"
    LIMITED = "limited"
    RESERVED_RECORDED = "reserved_recorded"
    IN_USE_RECORDED = "in_use_recorded"
    EXHAUSTED = "exhausted"
    RATE_LIMITED = "rate_limited"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"


class ResourceKind(str, Enum):
    """资源种类。

    作用：表达资源预算、调用预算、时间预算、配额、租约或并发配额等类别。
    边界：不读取 CPU、磁盘、网络、内存或任何真实系统资源。
    """

    UNKNOWN = "unknown"
    TOKEN_BUDGET = "token_budget"
    MODEL_CALL_BUDGET = "model_call_budget"
    TOOL_CALL_BUDGET = "tool_call_budget"
    TIME_BUDGET = "time_budget"
    MEMORY_BUDGET = "memory_budget"
    CPU_BUDGET = "cpu_budget"
    DISK_BUDGET = "disk_budget"
    NETWORK_BUDGET = "network_budget"
    FILE_ACCESS_QUOTA = "file_access_quota"
    TOOL_LEASE = "tool_lease"
    SANDBOX_QUOTA = "sandbox_quota"
    CONCURRENCY_QUOTA = "concurrency_quota"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class ResourceBudgetState:
    """资源预算状态。

    作用：记录外部给出的预算引用、资源类型、限制摘要、已用摘要和剩余摘要。
    边界：不扣减预算，不读取真实系统资源，不计算剩余额度。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    resource_status: ResourceStatus = ResourceStatus.UNKNOWN
    resource_kind: ResourceKind = ResourceKind.UNKNOWN
    budget_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    limit_snapshot: str | None = None
    used_snapshot: str | None = None
    remaining_snapshot: str | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("limit_snapshot", self.limit_snapshot),
            ("used_snapshot", self.used_snapshot),
            ("remaining_snapshot", self.remaining_snapshot),
        ):
            if value == "":
                raise ValueError(f"ResourceBudgetState.{name} cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ResourceBudgetState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class QuotaState:
    """资源配额状态。

    作用：记录外部配额引用、资源类型、作用对象、时间窗口和配额摘要。
    边界：不实现配额算法，不读取真实使用量，不扣减额度。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    resource_status: ResourceStatus = ResourceStatus.UNKNOWN
    quota_ref: TypedRef | None = None
    resource_kind: ResourceKind = ResourceKind.UNKNOWN
    subject_ref: TypedRef | None = None
    window_ref: TypedRef | None = None
    limit_snapshot: str | None = None
    used_snapshot: str | None = None
    source_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("limit_snapshot", self.limit_snapshot), ("used_snapshot", self.used_snapshot)):
            if value == "":
                raise ValueError(f"QuotaState.{name} cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("QuotaState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RateLimitState:
    """资源限速状态。

    作用：记录外部限速状态、重试时间引用、限速原因和适用对象引用。
    边界：不 sleep，不重试，不调度，不改变任务顺序。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    resource_status: ResourceStatus = ResourceStatus.UNKNOWN
    resource_kind: ResourceKind = ResourceKind.UNKNOWN
    quota_ref: TypedRef | None = None
    budget_ref: TypedRef | None = None
    retry_after_ref: TypedRef | None = None
    rate_limit_reason: str | None = None
    applies_to_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.rate_limit_reason == "":
            raise ValueError("RateLimitState.rate_limit_reason cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("RateLimitState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ResourceLeaseState:
    """资源租约状态。

    作用：记录外部资源租约、资源类型、作用对象、授予范围、过期引用和撤销原因。
    边界：不创建租约，不续租租约，不撤销真实租约，不持有可执行函数。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    resource_status: ResourceStatus = ResourceStatus.UNKNOWN
    resource_kind: ResourceKind = ResourceKind.UNKNOWN
    lease_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    tool_group_release_state_ref: TypedRef | None = None
    granted_scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    expires_at_ref: TypedRef | None = None
    revocation_reason: str | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.revocation_reason == "":
            raise ValueError("ResourceLeaseState.revocation_reason cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ResourceLeaseState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ResourcePressureState:
    """资源压力状态。

    作用：记录外部给出的预算紧张、并发受限或速率受限等资源压力事实。
    边界：不自动降级，不重排任务，不读取或计算真实资源压力。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    resource_status: ResourceStatus = ResourceStatus.UNKNOWN
    pressure_level: str | None = None
    resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affected_subject_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    suggested_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.pressure_level == "":
            raise ValueError("ResourcePressureState.pressure_level cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ResourcePressureState.schema_version cannot be empty")
