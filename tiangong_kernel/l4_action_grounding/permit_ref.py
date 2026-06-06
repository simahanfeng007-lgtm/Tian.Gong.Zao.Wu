"""L4 第二阶段动作许可引用对象。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .audit_requirement import AuditRequirementRef
from .boundary_ref import BoundaryDecisionRef, ConfirmationTicketRef, LeaseRef, PermissionGrantRef, PolicyDecisionRef, RiskReviewRef
from .credential_ref import CredentialHandleRef
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_expiry import PermitExpiry
from .permit_scope import PermitScope
from .resource_limit_ref import ResourceLimitRef


@dataclass(frozen=True, slots=True)
class PermitIssuerRef:
    issuer_ref: TypedRef
    issuer_hint: str = "future_l5"
    ref_only: bool = True
    l4_issuer: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.issuer_hint, "PermitIssuerRef.issuer_hint", 128)
        ensure_true(self.ref_only, "PermitIssuerRef.ref_only")
        ensure_false(self.l4_issuer, "PermitIssuerRef.l4_issuer")
        ensure_schema_version(self.schema_version, "PermitIssuerRef.schema_version")


@dataclass(frozen=True, slots=True)
class PermitSubjectRef:
    subject_ref: TypedRef
    ref_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "PermitSubjectRef.ref_only")
        ensure_schema_version(self.schema_version, "PermitSubjectRef.schema_version")


@dataclass(frozen=True, slots=True)
class PermitActionRef:
    action_ref: TypedRef
    ref_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "PermitActionRef.ref_only")
        ensure_schema_version(self.schema_version, "PermitActionRef.schema_version")


@dataclass(frozen=True, slots=True)
class PermitEnvironmentRef:
    environment_ref: TypedRef
    ref_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "PermitEnvironmentRef.ref_only")
        ensure_schema_version(self.schema_version, "PermitEnvironmentRef.schema_version")


@dataclass(frozen=True, slots=True)
class PermitConsumptionRef:
    consumption_ref: TypedRef
    summary_only: bool = True
    l4_consumed_real_resource: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.summary_only, "PermitConsumptionRef.summary_only")
        ensure_false(self.l4_consumed_real_resource, "PermitConsumptionRef.l4_consumed_real_resource")
        ensure_schema_version(self.schema_version, "PermitConsumptionRef.schema_version")


@dataclass(frozen=True, slots=True)
class ActionPermitRef:
    """未来 L5 动作许可引用。

    ref 只保存 scope/expiry/issuer/decision 等元数据；不保存凭据、不签发许可、不代表 L4 授权。
    """

    permit_ref: TypedRef
    scope: PermitScope | None = None
    expiry: PermitExpiry | None = None
    issuer_ref: PermitIssuerRef | None = None
    subject_ref: PermitSubjectRef | None = None
    action_ref: PermitActionRef | None = None
    environment_ref: PermitEnvironmentRef | None = None
    boundary_decision_ref: BoundaryDecisionRef | None = None
    policy_decision_ref: PolicyDecisionRef | None = None
    permission_grant_ref: PermissionGrantRef | None = None
    risk_review_ref: RiskReviewRef | None = None
    confirmation_ticket_ref: ConfirmationTicketRef | None = None
    lease_ref: LeaseRef | None = None
    credential_handle_ref: CredentialHandleRef | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    resource_limit_ref: ResourceLimitRef | None = None
    test_only: bool = False
    ref_only: bool = True
    l4_issued: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "ActionPermitRef.ref_only")
        ensure_false(self.l4_issued, "ActionPermitRef.l4_issued")
        ensure_schema_version(self.schema_version, "ActionPermitRef.schema_version")

    @property
    def is_structurally_complete(self) -> bool:
        return (
            self.scope is not None
            and self.expiry is not None
            and self.issuer_ref is not None
            and self.subject_ref is not None
            and self.action_ref is not None
        )


ExecutionPermitRef = ActionPermitRef
