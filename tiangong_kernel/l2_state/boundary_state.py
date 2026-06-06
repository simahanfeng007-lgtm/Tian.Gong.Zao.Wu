"""L2 边界检查状态对象。

作用：记录外部边界层给出的检查、阻断、降级和替代路径事实。
边界：不做风险评分，不做权限裁决，不发起确认，不执行恢复或替代路径。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class BoundaryCheckStatus(str, Enum):
    """边界检查结果状态。

    作用：表达外部边界层记录的通过、阻断、降级、替代路径或确认需求状态。
    边界：不代表 L2 自行通过、阻断、降级或要求确认。
    """

    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PASSED = "passed"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    ALTERNATIVE_AVAILABLE = "alternative_available"
    CONFIRMATION_REQUIRED = "confirmation_required"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED_TO_EVALUATE = "failed_to_evaluate"


class BoundaryBlockKind(str, Enum):
    """边界阻断种类。

    作用：表达外部边界层记录的策略、风险、隐私、资源或环境阻断类别。
    边界：不执行阻断，不恢复任务，不通知用户。
    """

    UNKNOWN = "unknown"
    POLICY_BLOCK = "policy_block"
    RISK_BLOCK = "risk_block"
    TRUST_BLOCK = "trust_block"
    PRIVACY_BLOCK = "privacy_block"
    SECRET_BLOCK = "secret_block"
    RESOURCE_BLOCK = "resource_block"
    ENVIRONMENT_BLOCK = "environment_block"
    SANDBOX_BLOCK = "sandbox_block"
    CONFIRMATION_MISSING = "confirmation_missing"
    SCOPE_VIOLATION = "scope_violation"
    UPPER_LAYER_REQUIRED = "upper_layer_required"


class BoundaryDegradeKind(str, Enum):
    """边界降级种类。

    作用：表达外部边界层记录的只读、摘要、范围收窄或人工复核等降级类别。
    边界：不改写执行计划，不替换工具组，不自动降级任务。
    """

    UNKNOWN = "unknown"
    READ_ONLY = "read_only"
    SUMMARY_ONLY = "summary_only"
    NO_EXTERNAL_NETWORK = "no_external_network"
    NO_FILE_WRITE = "no_file_write"
    NO_SECRET_ACCESS = "no_secret_access"
    NO_SUBPROCESS = "no_subprocess"
    LIMITED_TOOL_GROUP = "limited_tool_group"
    LIMITED_SCOPE = "limited_scope"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class BoundaryAlternativeKind(str, Enum):
    """边界替代路径种类。

    作用：表达外部边界层记录的只读、摘要、询问用户或低风险替代路径类别。
    边界：不自动选择替代路径，不改写 Skill、ToolGroup 或 ActionIntent。
    """

    UNKNOWN = "unknown"
    READ_ONLY_ALTERNATIVE = "read_only_alternative"
    SUMMARY_ALTERNATIVE = "summary_alternative"
    ASK_USER_ALTERNATIVE = "ask_user_alternative"
    LOWER_RISK_SKILL_ALTERNATIVE = "lower_risk_skill_alternative"
    WAIT_FOR_CONFIRMATION_ALTERNATIVE = "wait_for_confirmation_alternative"
    RETRY_WITH_LIMITED_SCOPE_ALTERNATIVE = "retry_with_limited_scope_alternative"
    OBSERVATION_ONLY_ALTERNATIVE = "observation_only_alternative"


@dataclass(frozen=True, slots=True)
class BoundaryCheckState:
    """边界检查状态。

    作用：记录某个 Skill、ToolGroup、ToolIntent、ActionIntent 或 EffectObservation 的边界检查事实。
    边界：不调用风险评分器，不调用权限系统，不生成确认票据。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    check_status: BoundaryCheckStatus = BoundaryCheckStatus.UNKNOWN
    checked_subject_ref: TypedRef | None = None
    boundary_ref: TypedRef | None = None
    risk_view_ref: TypedRef | None = None
    decision_ref: TypedRef | None = None
    policy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_code: str | None = None
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.reason_code == "":
            raise ValueError("BoundaryCheckState.reason_code cannot be empty when provided")
        if self.summary == "":
            raise ValueError("BoundaryCheckState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("BoundaryCheckState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryBlockedState:
    """边界阻断状态。

    作用：记录外部边界层给出的阻断种类、阻断对象、关联策略和风险裁决引用。
    边界：不执行回滚，不执行恢复，不通知用户，不做二次裁决。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    block_kind: BoundaryBlockKind = BoundaryBlockKind.UNKNOWN
    boundary_check_ref: TypedRef | None = None
    blocked_subject_ref: TypedRef | None = None
    blocking_policy_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    risk_decision_state_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recoverable: bool = False
    requires_upper_layer_action: bool = False
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("BoundaryBlockedState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("BoundaryBlockedState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryDegradedState:
    """边界降级状态。

    作用：记录外部边界层给出的降级种类、原对象、降级对象、允许范围和限制范围。
    边界：不替换工具组，不改写计划，不自动调整任务。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    degrade_kind: BoundaryDegradeKind = BoundaryDegradeKind.UNKNOWN
    boundary_check_ref: TypedRef | None = None
    original_subject_ref: TypedRef | None = None
    degraded_subject_ref: TypedRef | None = None
    allowed_scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    restricted_scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("BoundaryDegradedState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("BoundaryDegradedState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryAlternativeState:
    """边界替代路径状态。

    作用：记录外部边界层给出的替代对象、替代 Skill、替代工具组和确认需求引用。
    边界：不自动选择替代路径，不改写运行计划，不调用 Skill 或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    alternative_kind: BoundaryAlternativeKind = BoundaryAlternativeKind.UNKNOWN
    boundary_check_ref: TypedRef | None = None
    alternative_subject_ref: TypedRef | None = None
    alternative_skill_ref: TypedRef | None = None
    alternative_tool_group_ref: TypedRef | None = None
    requires_confirmation: bool = False
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("BoundaryAlternativeState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("BoundaryAlternativeState.schema_version cannot be empty")
