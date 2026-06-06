"""L4 第二阶段许可门控不变量。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class NoLiveActionWithoutL5PermitInvariant:
    invariant_ref: TypedRef
    l5_permit_required: bool = True
    live_action_without_l5_permit: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.l5_permit_required, "NoLiveActionWithoutL5PermitInvariant.l5_permit_required")
        ensure_false(self.live_action_without_l5_permit, "NoLiveActionWithoutL5PermitInvariant.live_action_without_l5_permit")
        ensure_schema_version(self.schema_version, "NoLiveActionWithoutL5PermitInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class TestOnlyPermitNeverProductionInvariant:
    __test__: ClassVar[bool] = False

    invariant_ref: TypedRef
    test_only_permit_allowed_in_production: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.test_only_permit_allowed_in_production, "TestOnlyPermitNeverProductionInvariant.test_only_permit_allowed_in_production")
        ensure_schema_version(self.schema_version, "TestOnlyPermitNeverProductionInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoL4PermissionDecisionInvariant:
    invariant_ref: TypedRef
    l4_permission_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_permission_decision_made, "NoL4PermissionDecisionInvariant.l4_permission_decision_made")
        ensure_schema_version(self.schema_version, "NoL4PermissionDecisionInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoL4RiskDecisionInvariant:
    invariant_ref: TypedRef
    l4_risk_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_risk_decision_made, "NoL4RiskDecisionInvariant.l4_risk_decision_made")
        ensure_schema_version(self.schema_version, "NoL4RiskDecisionInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoL4TicketIssuerInvariant:
    invariant_ref: TypedRef
    l4_ticket_issued: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_ticket_issued, "NoL4TicketIssuerInvariant.l4_ticket_issued")
        ensure_schema_version(self.schema_version, "NoL4TicketIssuerInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoL4CredentialResolverInvariant:
    invariant_ref: TypedRef
    l4_resolved_credential: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_resolved_credential, "NoL4CredentialResolverInvariant.l4_resolved_credential")
        ensure_schema_version(self.schema_version, "NoL4CredentialResolverInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoL4AuditWriterInvariant:
    invariant_ref: TypedRef
    l4_audit_written: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_audit_written, "NoL4AuditWriterInvariant.l4_audit_written")
        ensure_schema_version(self.schema_version, "NoL4AuditWriterInvariant.schema_version")
