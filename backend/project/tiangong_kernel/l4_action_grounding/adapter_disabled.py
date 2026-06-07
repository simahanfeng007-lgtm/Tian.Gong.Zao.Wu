"""Disabled reason objects for L4 adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class AdapterDisabledReasonKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    PRODUCTION_DISABLED = "production_disabled"
    TEST_ONLY_BLOCKED = "test_only_blocked"
    L5_PERMIT_REQUIRED = "l5_permit_required"
    STRUCTURE_MISMATCH = "structure_mismatch"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


@dataclass(frozen=True, slots=True)
class AdapterDisabledReason:
    """Declarative disabled reason; it does not perform recovery."""

    reason_ref: TypedRef
    reason_kind: AdapterDisabledReasonKind = AdapterDisabledReasonKind.DISABLED_BY_DEFAULT
    adapter_id: str = ""
    message: str = "adapter disabled in L4 phase 3"
    permanent_for_phase3: bool = True
    real_action_enabled: bool = False
    reason_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_id, "AdapterDisabledReason.adapter_id", 128)
        ensure_short_text(self.message, "AdapterDisabledReason.message")
        ensure_true(self.permanent_for_phase3, "AdapterDisabledReason.permanent_for_phase3")
        ensure_false(self.real_action_enabled, "AdapterDisabledReason.real_action_enabled")
        ensure_true(self.reason_only, "AdapterDisabledReason.reason_only")
        ensure_schema_version(self.schema_version, "AdapterDisabledReason.schema_version")
