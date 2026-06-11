"""Adapter status objects for L4 action grounding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class AdapterStatusKind(str, Enum):
    DECLARED = "declared"
    REGISTERED = "registered"
    AVAILABLE_FOR_STRUCTURE = "available_for_structure"
    DISABLED = "disabled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class AdapterStatus:
    """Adapter status fact; it never marks a real action as enabled."""

    status_ref: TypedRef
    adapter_id: str
    status_kind: AdapterStatusKind = AdapterStatusKind.DECLARED
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    enabled_by_default: bool = False
    production_enabled: bool = False
    real_action_enabled: bool = False
    status_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_id, "AdapterStatus.adapter_id", 128)
        for item in self.reason_codes:
            ensure_short_text(item, "AdapterStatus.reason_codes", 128)
        ensure_false(self.production_enabled, "AdapterStatus.production_enabled")
        ensure_false(self.real_action_enabled, "AdapterStatus.real_action_enabled")
        ensure_true(self.status_only, "AdapterStatus.status_only")
        ensure_schema_version(self.schema_version, "AdapterStatus.schema_version")
