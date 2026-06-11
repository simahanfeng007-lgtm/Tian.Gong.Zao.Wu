"""Disabled-by-default declarations for external action grounding."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExternalActionDisabledByDefault:
    """All live external actions stay disabled until future L5/L6 integration."""

    disabled_ref: TypedRef
    action_kind: str
    reason: str = "live external action disabled by default"
    requires_l5_permit: bool = True
    enabled_by_default: bool = False
    production_enabled: bool = False
    real_action_enabled: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "ExternalActionDisabledByDefault.action_kind", 128)
        ensure_short_text(self.reason, "ExternalActionDisabledByDefault.reason")
        ensure_true(self.requires_l5_permit, "ExternalActionDisabledByDefault.requires_l5_permit")
        ensure_false(self.enabled_by_default, "ExternalActionDisabledByDefault.enabled_by_default")
        ensure_false(self.production_enabled, "ExternalActionDisabledByDefault.production_enabled")
        ensure_false(self.real_action_enabled, "ExternalActionDisabledByDefault.real_action_enabled")
        ensure_schema_version(self.schema_version, "ExternalActionDisabledByDefault.schema_version")
