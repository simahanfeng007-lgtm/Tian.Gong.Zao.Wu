"""L4 第二阶段边界与许可相关引用对象。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_scope import PermitScope


class BoundaryDecisionStatus(str, Enum):
    """未来 L5 边界裁决引用状态。"""

    REFERENCED = "referenced"
    GRANTED = "granted"
    DENIED = "denied"
    CONFIRMATION_REQUIRED = "confirmation_required"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class BoundaryDecisionRef:
    decision_ref: TypedRef
    decision_status: BoundaryDecisionStatus = BoundaryDecisionStatus.REFERENCED
    scope: PermitScope | None = None
    reason_ref: TypedRef | None = None
    explicit_expired: bool = False
    ref_only: bool = True
    l4_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "BoundaryDecisionRef.ref_only")
        ensure_false(self.l4_decision_made, "BoundaryDecisionRef.l4_decision_made")
        ensure_schema_version(self.schema_version, "BoundaryDecisionRef.schema_version")

    @property
    def is_expired(self) -> bool:
        return self.explicit_expired


@dataclass(frozen=True, slots=True)
class PolicyDecisionRef:
    decision_ref: TypedRef
    policy_scope_hint: str = "future_l5_policy_decision_ref"
    ref_only: bool = True
    l4_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.policy_scope_hint, "PolicyDecisionRef.policy_scope_hint", 128)
        ensure_true(self.ref_only, "PolicyDecisionRef.ref_only")
        ensure_false(self.l4_decision_made, "PolicyDecisionRef.l4_decision_made")
        ensure_schema_version(self.schema_version, "PolicyDecisionRef.schema_version")


@dataclass(frozen=True, slots=True)
class PermissionGrantRef:
    grant_ref: TypedRef
    grant_scope: PermitScope | None = None
    ref_only: bool = True
    l4_grant_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "PermissionGrantRef.ref_only")
        ensure_false(self.l4_grant_made, "PermissionGrantRef.l4_grant_made")
        ensure_schema_version(self.schema_version, "PermissionGrantRef.schema_version")


@dataclass(frozen=True, slots=True)
class RiskReviewRef:
    review_ref: TypedRef
    risk_status_hint: str = "future_l5_risk_review_ref"
    ref_only: bool = True
    l4_risk_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.risk_status_hint, "RiskReviewRef.risk_status_hint", 128)
        ensure_true(self.ref_only, "RiskReviewRef.ref_only")
        ensure_false(self.l4_risk_decision_made, "RiskReviewRef.l4_risk_decision_made")
        ensure_schema_version(self.schema_version, "RiskReviewRef.schema_version")


@dataclass(frozen=True, slots=True)
class ConfirmationTicketRef:
    ticket_ref: TypedRef
    confirmation_required: bool = False
    confirmed_by_l5: bool = False
    ref_only: bool = True
    l4_ticket_issued: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "ConfirmationTicketRef.ref_only")
        ensure_false(self.l4_ticket_issued, "ConfirmationTicketRef.l4_ticket_issued")
        ensure_schema_version(self.schema_version, "ConfirmationTicketRef.schema_version")


@dataclass(frozen=True, slots=True)
class LeaseRef:
    lease_ref: TypedRef
    explicit_expired: bool = False
    ref_only: bool = True
    l4_lease_granted: bool = False
    l4_lease_extended: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "LeaseRef.ref_only")
        ensure_false(self.l4_lease_granted, "LeaseRef.l4_lease_granted")
        ensure_false(self.l4_lease_extended, "LeaseRef.l4_lease_extended")
        ensure_schema_version(self.schema_version, "LeaseRef.schema_version")

    @property
    def is_expired(self) -> bool:
        return self.explicit_expired
