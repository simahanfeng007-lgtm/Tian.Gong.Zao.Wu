"""Adapter identity and descriptor objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_mode import AdapterMode
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AdapterIdentity:
    """Stable adapter identity; not a process, worker, or subsystem."""

    adapter_ref: TypedRef
    adapter_id: str
    adapter_kind: str = "no_op"
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_id, "AdapterIdentity.adapter_id", 128)
        ensure_short_text(self.adapter_kind, "AdapterIdentity.adapter_kind", 128)
        ensure_schema_version(self.schema_version, "AdapterIdentity.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    """Declarative adapter descriptor; it describes, never authorizes."""

    identity: AdapterIdentity
    adapter_name: str
    version: str = "0.1"
    mode: AdapterMode = AdapterMode.NO_OP
    capability_descriptor: AdapterCapabilityDescriptor | None = None
    risk_surface_descriptor: AdapterRiskSurfaceDescriptor | None = None
    supported_action_kinds: tuple[str, ...] = field(default_factory=tuple)
    supported_envelope_types: tuple[str, ...] = ("adapter_input",)
    requires_l5_permit: bool = False
    requires_credential_handle: bool = False
    supports_dry_run: bool = False
    supports_fake: bool = False
    supports_no_op: bool = False
    enabled_by_default: bool = True
    production_enabled: bool = False
    test_only: bool = False
    side_effect_declared: str = "none"
    reversibility_declared: str = "not_applicable"
    resource_usage_declared: str = "none"
    audit_requirement_declared: str = "none"
    subsystem_dependency_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    descriptor_only: bool = True
    l4_grants_permission: bool = False
    l4_scores_risk: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_name, "AdapterDescriptor.adapter_name", 128)
        ensure_short_text(self.version, "AdapterDescriptor.version", 64)
        for item in self.supported_action_kinds + self.supported_envelope_types:
            ensure_short_text(item, "AdapterDescriptor support text", 128)
        ensure_short_text(self.side_effect_declared, "AdapterDescriptor.side_effect_declared", 128)
        ensure_short_text(self.reversibility_declared, "AdapterDescriptor.reversibility_declared", 128)
        ensure_short_text(self.resource_usage_declared, "AdapterDescriptor.resource_usage_declared", 128)
        ensure_short_text(self.audit_requirement_declared, "AdapterDescriptor.audit_requirement_declared", 128)
        ensure_true(self.descriptor_only, "AdapterDescriptor.descriptor_only")
        ensure_false(self.l4_grants_permission, "AdapterDescriptor.l4_grants_permission")
        ensure_false(self.l4_scores_risk, "AdapterDescriptor.l4_scores_risk")
        ensure_schema_version(self.schema_version, "AdapterDescriptor.schema_version")

    @property
    def adapter_id(self) -> str:
        return self.identity.adapter_id

    @property
    def adapter_kind(self) -> str:
        return self.identity.adapter_kind

    def is_structurally_complete(self) -> bool:
        return self.capability_descriptor is not None and self.risk_surface_descriptor is not None

    def structurally_supports(self, action_kind: str, envelope_type: str, mode: AdapterMode) -> bool:
        """Check descriptor structure only; no permission or risk decision."""

        if self.capability_descriptor is None:
            return False
        if not self.capability_descriptor.structurally_supports(action_kind, envelope_type, mode):
            return False
        return action_kind in self.supported_action_kinds and envelope_type in self.supported_envelope_types
