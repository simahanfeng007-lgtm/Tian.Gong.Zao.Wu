"""No boundary bypass guarantee for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_BOUNDARY_SURFACES, L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4NoBoundaryBypassGuarantee:
    """Guarantee that L4 does not bypass L5 boundary ownership."""

    guarantee_ref: TypedRef
    covered_boundaries: tuple[str, ...] = field(default_factory=lambda: L4_BOUNDARY_SURFACES)
    guarantee_only: bool = True
    makes_policy_decision: bool = False
    makes_risk_decision: bool = False
    issues_permit: bool = False
    generates_confirmation_ticket: bool = False
    grants_lease: bool = False
    resolves_credential: bool = False
    extends_resource_budget: bool = False
    authorizes_concurrency: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.covered_boundaries, "L4NoBoundaryBypassGuarantee.covered_boundaries", 128)
        ensure_true(self.guarantee_only, "L4NoBoundaryBypassGuarantee.guarantee_only")
        ensure_false(self.makes_policy_decision, "L4NoBoundaryBypassGuarantee.makes_policy_decision")
        ensure_false(self.makes_risk_decision, "L4NoBoundaryBypassGuarantee.makes_risk_decision")
        ensure_false(self.issues_permit, "L4NoBoundaryBypassGuarantee.issues_permit")
        ensure_false(self.generates_confirmation_ticket, "L4NoBoundaryBypassGuarantee.generates_confirmation_ticket")
        ensure_false(self.grants_lease, "L4NoBoundaryBypassGuarantee.grants_lease")
        ensure_false(self.resolves_credential, "L4NoBoundaryBypassGuarantee.resolves_credential")
        ensure_false(self.extends_resource_budget, "L4NoBoundaryBypassGuarantee.extends_resource_budget")
        ensure_false(self.authorizes_concurrency, "L4NoBoundaryBypassGuarantee.authorizes_concurrency")
        ensure_schema_version(self.schema_version, "L4NoBoundaryBypassGuarantee.schema_version")
