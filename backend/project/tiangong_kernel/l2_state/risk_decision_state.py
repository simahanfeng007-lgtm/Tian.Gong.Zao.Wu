"""L2 风险、策略和裁决引用状态对象。

作用：记录外部风险视图、策略引用和裁决记录的状态事实。
边界：不计算风险分数，不执行策略匹配，不做放行或阻断裁决，不发起确认。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class RiskDecisionStatus(str, Enum):
    """风险与裁决记录状态。

    作用：表达外部风险视图或外部裁决结果已被记录的状态标签。
    边界：不代表 L2 进行风险计算、权限裁决或确认流程。
    """

    UNKNOWN = "unknown"
    RISK_VIEW_OBSERVED = "risk_view_observed"
    DECISION_OBSERVED = "decision_observed"
    ALLOW_RECORDED = "allow_recorded"
    DENY_RECORDED = "deny_recorded"
    CONFIRMATION_REQUIRED_RECORDED = "confirmation_required_recorded"
    ESCALATION_RECORDED = "escalation_recorded"
    OVERRIDE_RECORDED = "override_recorded"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class RiskSeverityLabel(str, Enum):
    """风险等级标签。

    作用：表达外部风险视图给出的 A0 至 A5 或自定义风险标签。
    边界：不从标签推导执行许可，A5 也只是状态标签和引用。
    """

    UNKNOWN = "unknown"
    A0 = "a0"
    A1 = "a1"
    A2 = "a2"
    A3 = "a3"
    A4 = "a4"
    A5 = "a5"
    CUSTOM = "custom"


class PolicyReferenceStatus(str, Enum):
    """策略引用状态。

    作用：表达策略被引用、匹配、未匹配、废弃或缺失的外部记录状态。
    边界：不执行策略匹配，不导入策略引擎，不做权限裁决。
    """

    UNKNOWN = "unknown"
    REFERENCED = "referenced"
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class RiskDecisionState:
    """风险与裁决引用状态。

    作用：记录外部风险视图引用、风险等级标签、外部裁决引用、策略引用和证据引用。
    边界：不计算风险分数，不改变风险等级，不发起确认，不做二次裁决。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    decision_status: RiskDecisionStatus = RiskDecisionStatus.UNKNOWN
    severity_label: RiskSeverityLabel = RiskSeverityLabel.UNKNOWN
    subject_ref: TypedRef | None = None
    risk_view_ref: TypedRef | None = None
    decision_ref: TypedRef | None = None
    policy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_check_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    score_snapshot_ref: TypedRef | None = None
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("RiskDecisionState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("RiskDecisionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PolicyReferenceState:
    """策略引用状态。

    作用：记录策略引用、策略名称、版本引用、适用对象和来源边界引用。
    边界：不保存完整策略正文，不执行策略匹配，不导入策略或权限系统。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    reference_status: PolicyReferenceStatus = PolicyReferenceStatus.UNKNOWN
    policy_ref: TypedRef | None = None
    policy_name: str | None = None
    policy_version_ref: TypedRef | None = None
    applies_to_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_boundary_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.policy_name == "":
            raise ValueError("PolicyReferenceState.policy_name cannot be empty when provided")
        if self.policy_name is not None and ("\n" in self.policy_name or len(self.policy_name) > 128):
            raise ValueError("PolicyReferenceState.policy_name must be a short label")
        if self.summary == "":
            raise ValueError("PolicyReferenceState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("PolicyReferenceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DecisionRecordState:
    """外部裁决记录状态。

    作用：记录外部裁决引用、裁决来源、裁决对象和过期引用。
    边界：不实现裁决引擎，不做放行或阻断判断，不发起确认。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recorded_status: RiskDecisionStatus = RiskDecisionStatus.UNKNOWN
    decision_ref: TypedRef | None = None
    decision_source_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    expires_at_ref: TypedRef | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("DecisionRecordState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("DecisionRecordState.schema_version cannot be empty")
