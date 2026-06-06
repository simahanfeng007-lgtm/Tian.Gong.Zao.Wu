"""Declarative adapter risk-surface descriptors."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AdapterRiskSurfaceDescriptor:
    """Risk-surface facts; this object never scores or releases risk."""

    risk_surface_ref: TypedRef
    side_effect_declared: str = "none"
    reversibility_declared: str = "not_applicable"
    resource_usage_declared: str = "none"
    audit_requirement_declared: str = "none"
    credential_requirement_declared: str = "none"
    subsystem_dependency_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    risk_surface_only: bool = True
    l4_scores_risk: bool = False
    l4_releases_risk: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.side_effect_declared, "AdapterRiskSurfaceDescriptor.side_effect_declared", 128)
        ensure_short_text(self.reversibility_declared, "AdapterRiskSurfaceDescriptor.reversibility_declared", 128)
        ensure_short_text(self.resource_usage_declared, "AdapterRiskSurfaceDescriptor.resource_usage_declared", 128)
        ensure_short_text(self.audit_requirement_declared, "AdapterRiskSurfaceDescriptor.audit_requirement_declared", 128)
        ensure_short_text(self.credential_requirement_declared, "AdapterRiskSurfaceDescriptor.credential_requirement_declared", 128)
        ensure_true(self.risk_surface_only, "AdapterRiskSurfaceDescriptor.risk_surface_only")
        ensure_false(self.l4_scores_risk, "AdapterRiskSurfaceDescriptor.l4_scores_risk")
        ensure_false(self.l4_releases_risk, "AdapterRiskSurfaceDescriptor.l4_releases_risk")
        ensure_schema_version(self.schema_version, "AdapterRiskSurfaceDescriptor.schema_version")
