"""Network action failures for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class NetworkActionFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    PERMIT_MISSING = "permit_missing"
    DOMAIN_SCOPE_MISMATCH = "domain_scope_mismatch"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    CREDENTIAL_REQUIRED = "credential_required"
    NETWORK_BLOCKED = "network_blocked"
    SENSITIVE_DATA_BLOCKED = "sensitive_data_blocked"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


@dataclass(frozen=True, slots=True)
class NetworkActionFailure:
    """Standard network action failure; no network access is performed."""

    failure_ref: TypedRef
    request_ref: TypedRef
    failure_kind: NetworkActionFailureKind = NetworkActionFailureKind.DISABLED_BY_DEFAULT
    message: str = "network action disabled by default"
    blocked_invariant_names: tuple[str, ...] = field(default_factory=tuple)
    boundary_feedback_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    requires_l5_permit: bool = True
    real_network_access: bool = False
    sends_payload: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    retryable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "NetworkActionFailure.message")
        for item in self.blocked_invariant_names:
            ensure_short_text(item, "NetworkActionFailure.blocked_invariant_names", 128)
        ensure_true(self.requires_l5_permit, "NetworkActionFailure.requires_l5_permit")
        ensure_false(self.real_network_access, "NetworkActionFailure.real_network_access")
        ensure_false(self.sends_payload, "NetworkActionFailure.sends_payload")
        ensure_false(self.writes_l2_state, "NetworkActionFailure.writes_l2_state")
        ensure_false(self.writes_audit_store, "NetworkActionFailure.writes_audit_store")
        ensure_false(self.retryable, "NetworkActionFailure.retryable")
        ensure_schema_version(self.schema_version, "NetworkActionFailure.schema_version")
