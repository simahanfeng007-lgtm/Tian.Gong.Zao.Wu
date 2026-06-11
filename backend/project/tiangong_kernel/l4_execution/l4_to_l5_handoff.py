"""L4 to L5 handoff envelope for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_BOUNDARY_SURFACES, L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5HandoffEnvelope:
    """Handoff envelope only; it implements no L5 boundary layer."""

    handoff_ref: TypedRef
    permit_ref: TypedRef | None = None
    boundary_feedback_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    concurrency_scope_ref: TypedRef | None = None
    audit_chain_ref: TypedRef | None = None
    privacy_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    data_governance_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    external_disclosure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    credential_token_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    token_revocation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    credential_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    plugin_host_requirement_ref: TypedRef | None = None
    quality_gate_ref: TypedRef | None = None
    version_switch_requirement_ref: TypedRef | None = None
    required_l5_surfaces: tuple[str, ...] = field(default_factory=lambda: L4_BOUNDARY_SURFACES)
    handoff_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    envelope_only: bool = True
    implements_l5: bool = False
    grants_permission: bool = False
    emits_plain_credential: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_l5_surfaces, "L4ToL5HandoffEnvelope.required_l5_surfaces", 128)
        ensure_pair_items(self.handoff_items, "L4ToL5HandoffEnvelope.handoff_items")
        ensure_true(self.envelope_only, "L4ToL5HandoffEnvelope.envelope_only")
        ensure_false(self.implements_l5, "L4ToL5HandoffEnvelope.implements_l5")
        ensure_false(self.grants_permission, "L4ToL5HandoffEnvelope.grants_permission")
        ensure_false(self.emits_plain_credential, "L4ToL5HandoffEnvelope.emits_plain_credential")
        ensure_schema_version(self.schema_version, "L4ToL5HandoffEnvelope.schema_version")
