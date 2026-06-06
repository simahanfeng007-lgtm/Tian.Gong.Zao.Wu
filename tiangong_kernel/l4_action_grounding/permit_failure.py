"""L4 第二阶段许可、凭据、资源与审计失败对象。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .error import ActionGroundingError, ActionGroundingErrorKind
from .failure import ActionGroundingFailure, ActionGroundingFailureKind
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class PermitFailureKind(str, Enum):
    PERMIT_MISSING = "permit_missing"
    PERMIT_DENIED = "permit_denied"
    PERMIT_EXPIRED = "permit_expired"
    PERMIT_SCOPE_MISMATCH = "permit_scope_mismatch"
    PERMIT_MALFORMED = "permit_malformed"
    PERMIT_TEST_ONLY_MISUSE = "permit_test_only_misuse"
    LEASE_UNAVAILABLE = "lease_unavailable"
    CREDENTIAL_UNAVAILABLE = "credential_unavailable"
    CREDENTIAL_SCOPE_MISMATCH = "credential_scope_mismatch"
    RESOURCE_LIMIT_UNAVAILABLE = "resource_limit_unavailable"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    AUDIT_REQUIREMENT_MISSING = "audit_requirement_missing"


@dataclass(frozen=True, slots=True)
class PermitFailure:
    """许可门控失败基类；只表达失败原因，不执行补救动作。"""

    failure_ref: TypedRef
    failure_kind: PermitFailureKind
    reason_summary: str
    source_request_ref: TypedRef | None = None
    l5_permit_required: bool = True
    live_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.reason_summary, "PermitFailure.reason_summary")
        ensure_true(self.l5_permit_required, "PermitFailure.l5_permit_required")
        ensure_false(self.live_action_performed, "PermitFailure.live_action_performed")
        ensure_schema_version(self.schema_version, "PermitFailure.schema_version")

    def to_action_failure(self) -> ActionGroundingFailure:
        return ActionGroundingFailure(
            failure_ref=self.failure_ref,
            failure_kind=ActionGroundingFailureKind.BOUNDARY_PERMIT_REQUIRED,
            reason_summary=self.reason_summary,
            source_request_ref=self.source_request_ref,
            error=ActionGroundingError(
                error_kind=ActionGroundingErrorKind.PERMIT_REQUIRED,
                message=self.reason_summary,
            ),
            blocked_invariant_names=("NoLiveActionWithoutL5PermitInvariant",),
            l5_permit_required=self.l5_permit_required,
            live_action_performed=self.live_action_performed,
        )


@dataclass(frozen=True, slots=True)
class PermitMissingFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_MISSING
    reason_summary: str = "future L5 permit ref is missing"


@dataclass(frozen=True, slots=True)
class PermitDeniedFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_DENIED
    reason_summary: str = "future L5 permit ref is denied by referenced boundary decision"


@dataclass(frozen=True, slots=True)
class PermitExpiredFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_EXPIRED
    reason_summary: str = "future L5 permit ref is explicitly expired"


@dataclass(frozen=True, slots=True)
class PermitScopeMismatchFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_SCOPE_MISMATCH
    reason_summary: str = "future L5 permit scope does not structurally cover requested scope"


@dataclass(frozen=True, slots=True)
class PermitMalformedFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_MALFORMED
    reason_summary: str = "future L5 permit ref is structurally incomplete"


@dataclass(frozen=True, slots=True)
class PermitTestOnlyMisuseFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.PERMIT_TEST_ONLY_MISUSE
    reason_summary: str = "test-only permit cannot be used on production path"


@dataclass(frozen=True, slots=True)
class LeaseUnavailableFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.LEASE_UNAVAILABLE
    reason_summary: str = "lease ref is unavailable or explicitly expired"


@dataclass(frozen=True, slots=True)
class CredentialUnavailableFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.CREDENTIAL_UNAVAILABLE
    reason_summary: str = "credential handle ref is unavailable"


@dataclass(frozen=True, slots=True)
class CredentialScopeMismatchFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.CREDENTIAL_SCOPE_MISMATCH
    reason_summary: str = "credential handle scope does not structurally cover requested scope"


@dataclass(frozen=True, slots=True)
class ResourceLimitUnavailableFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.RESOURCE_LIMIT_UNAVAILABLE
    reason_summary: str = "resource limit ref is unavailable"


@dataclass(frozen=True, slots=True)
class ResourceLimitExceededFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.RESOURCE_LIMIT_EXCEEDED
    reason_summary: str = "resource limit ref reports exceeded status"


@dataclass(frozen=True, slots=True)
class AuditRequirementMissingFailure(PermitFailure):
    failure_kind: PermitFailureKind = PermitFailureKind.AUDIT_REQUIREMENT_MISSING
    reason_summary: str = "audit requirement ref is missing"
