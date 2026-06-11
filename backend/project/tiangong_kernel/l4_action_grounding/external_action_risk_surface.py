"""Rimockkey_surface descriptors for external actions."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExternalActionRiskSurface:
    """Describe risk surfaces; it does not score or allow risk."""

    risk_surface_ref: TypedRef
    summary: str = "external action risk surface"
    filesystem: bool = False
    network: bool = False
    terminal: bool = False
    desktop: bool = False
    credential: bool = False
    privacy: bool = False
    persistence: bool = False
    destructive: bool = False
    descriptor_only: bool = True
    risk_decision_made: bool = False
    permission_granted: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "ExternalActionRiskSurface.summary")
        ensure_true(self.descriptor_only, "ExternalActionRiskSurface.descriptor_only")
        ensure_false(self.risk_decision_made, "ExternalActionRiskSurface.risk_decision_made")
        ensure_false(self.permission_granted, "ExternalActionRiskSurface.permission_granted")
        ensure_schema_version(self.schema_version, "ExternalActionRiskSurface.schema_version")
