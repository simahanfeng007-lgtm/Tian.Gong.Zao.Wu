"""Adapter failure normalization objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef

from .adapter_envelope import AdapterFailureEnvelope
from .adapter_mode import AdapterMode
from .failure import ActionGroundingFailure, ActionGroundingFailureKind
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text


class AdapterFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    NOT_FOUND = "not_found"
    CAPABILITY_MISMATCH = "capability_mismatch"
    MODE_MISMATCH = "mode_mismatch"
    PRODUCTION_DISABLED = "production_disabled"
    TEST_ONLY_MODE = "test_only_mode"
    PERMIT_REQUIRED = "permit_required"
    SCOPE_MISMATCH = "scope_mismatch"
    INVARIANT_VIOLATION = "invariant_violation"
    MALFORMED_DESCRIPTOR = "malformed_descriptor"
    DUPLICATE_ADAPTER_ID = "duplicate_adapter_id"
    CREDENTIAL_FORBIDDEN = "credential_forbidden"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


def new_adapter_typed_ref(ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{uuid4().hex}"), ref_type)


@dataclass(frozen=True, slots=True)
class AdapterFailure:
    """Standard adapter failure; no bare exception is a business result."""

    failure_ref: TypedRef
    failure_kind: AdapterFailureKind = AdapterFailureKind.DISABLED_BY_DEFAULT
    message: str = "adapter rejected by L4 phase 3 structural rule"
    adapter_id: str = ""
    adapter_kind: str = ""
    action_kind: str = ""
    mode: AdapterMode = AdapterMode.NO_OP
    recoverability_hint: str = "replan_or_stop"
    boundary_recheck_required_hint: bool = False
    retry_allowed_hint: bool = False
    real_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (
            self.message,
            self.adapter_id,
            self.adapter_kind,
            self.action_kind,
            self.recoverability_hint,
        ):
            ensure_short_text(value, "AdapterFailure text")
        ensure_false(self.retry_allowed_hint, "AdapterFailure.retry_allowed_hint")
        ensure_false(self.real_action_performed, "AdapterFailure.real_action_performed")
        ensure_schema_version(self.schema_version, "AdapterFailure.schema_version")

    def to_envelope(self) -> AdapterFailureEnvelope:
        return AdapterFailureEnvelope(
            failure_ref=self.failure_ref,
            adapter_id=self.adapter_id,
            adapter_kind=self.adapter_kind,
            action_kind=self.action_kind,
            mode=self.mode,
            failure_category="adapter",
            failure_code=self.failure_kind.value,
            message=self.message,
            recoverability_hint=self.recoverability_hint,
            retry_allowed_hint=False,
            replan_required_hint=True,
            boundary_recheck_required_hint=self.boundary_recheck_required_hint,
        )

    def to_action_failure(self) -> ActionGroundingFailure:
        kind = (
            ActionGroundingFailureKind.REAL_ACTION_FORBIDDEN
            if self.failure_kind in {AdapterFailureKind.PRODUCTION_DISABLED, AdapterFailureKind.REAL_ACTION_FORBIDDEN}
            else ActionGroundingFailureKind.STRUCTURE_INVALID
        )
        return ActionGroundingFailure(
            failure_ref=self.failure_ref,
            failure_kind=kind,
            reason_summary=self.message,
            blocked_invariant_names=(self.failure_kind.value,),
            l5_permit_required=self.failure_kind == AdapterFailureKind.PERMIT_REQUIRED,
            live_action_performed=False,
            retryable=False,
        )


@dataclass(frozen=True, slots=True)
class AdapterDisabledByDefaultFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.DISABLED_BY_DEFAULT


@dataclass(frozen=True, slots=True)
class AdapterNotFoundFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.NOT_FOUND


@dataclass(frozen=True, slots=True)
class AdapterCapabilityMismatchFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.CAPABILITY_MISMATCH


@dataclass(frozen=True, slots=True)
class AdapterModeMismatchFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.MODE_MISMATCH


@dataclass(frozen=True, slots=True)
class AdapterProductionDisabledFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.PRODUCTION_DISABLED


@dataclass(frozen=True, slots=True)
class AdapterTestOnlyModeFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.TEST_ONLY_MODE


@dataclass(frozen=True, slots=True)
class AdapterPermitRequiredFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.PERMIT_REQUIRED


@dataclass(frozen=True, slots=True)
class AdapterScopeMismatchFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.SCOPE_MISMATCH


@dataclass(frozen=True, slots=True)
class AdapterInvariantViolationFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.INVARIANT_VIOLATION


@dataclass(frozen=True, slots=True)
class AdapterMalformedDescriptorFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.MALFORMED_DESCRIPTOR


@dataclass(frozen=True, slots=True)
class AdapterDuplicateIdFailure(AdapterFailure):
    failure_kind: AdapterFailureKind = AdapterFailureKind.DUPLICATE_ADAPTER_ID


AdapterSelectionFailure = AdapterFailure
