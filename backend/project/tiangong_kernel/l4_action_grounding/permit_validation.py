"""L4 第二阶段许可结构校验结果。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class PermitValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONFIRMATION_REQUIRED = "confirmation_required"
    DEGRADED = "degraded"
    MALFORMED = "malformed"
    TEST_ONLY_REJECTED = "test_only_rejected"


class PermitValidationReason(str, Enum):
    STRUCTURE_ACCEPTED = "structure_accepted"
    PERMIT_MISSING = "permit_missing"
    PERMIT_MALFORMED = "permit_malformed"
    PERMIT_EXPIRED = "permit_expired"
    SCOPE_MISMATCH = "scope_mismatch"
    TEST_ONLY_MISUSE = "test_only_misuse"
    BOUNDARY_DENIED = "boundary_denied"
    CONFIRMATION_REQUIRED = "confirmation_required"
    LEASE_UNAVAILABLE = "lease_unavailable"
    CREDENTIAL_UNAVAILABLE = "credential_unavailable"
    RESOURCE_LIMIT_UNAVAILABLE = "resource_limit_unavailable"
    AUDIT_REQUIREMENT_MISSING = "audit_requirement_missing"


@dataclass(frozen=True, slots=True)
class PermitValidationTrace:
    trace_ref: TypedRef
    checked_step_names: tuple[str, ...] = field(default_factory=tuple)
    trace_only: bool = True
    l4_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.checked_step_names:
            ensure_short_text(item, "PermitValidationTrace.checked_step_names", 128)
        ensure_true(self.trace_only, "PermitValidationTrace.trace_only")
        ensure_false(self.l4_decision_made, "PermitValidationTrace.l4_decision_made")
        ensure_schema_version(self.schema_version, "PermitValidationTrace.schema_version")


@dataclass(frozen=True, slots=True)
class PermitValidationResult:
    result_ref: TypedRef
    status: PermitValidationStatus
    reason: PermitValidationReason
    allowed_for_grounding: bool = False
    structurally_accepted_for_grounding: bool = False
    is_authorization: bool = False
    authorization_source_ref: TypedRef | None = None
    requires_boundary_authorization: bool = True
    reason_summary: str = ""
    validation_trace: PermitValidationTrace | None = None
    validation_only: bool = True
    l4_authorized_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.reason_summary, "PermitValidationResult.reason_summary")
        ensure_false(self.is_authorization, "PermitValidationResult.is_authorization")
        ensure_true(self.validation_only, "PermitValidationResult.validation_only")
        ensure_false(self.l4_authorized_action, "PermitValidationResult.l4_authorized_action")
        ensure_schema_version(self.schema_version, "PermitValidationResult.schema_version")
