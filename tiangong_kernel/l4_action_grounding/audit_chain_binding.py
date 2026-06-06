"""Audit evidence responsibility chain bindings for L4.

These objects are ref-only carriers. L4 records no audit event, stores no
evidence, and verifies no integrity proof.
"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ActionAuditChain:
    """Complete audit/evidence/responsibility reference chain for one L4 action."""

    chain_ref: TypedRef
    event_requirement_ref: TypedRef | None = None
    event_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    responsibility_chain_ref: TypedRef | None = None
    accountability_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    tamper_evidence_ref: TypedRef | None = None
    integrity_chain_ref: TypedRef | None = None
    ref_only: bool = True
    l4_writes_event: bool = False
    l4_writes_audit: bool = False
    stores_evidence: bool = False
    verifies_tamper: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "L4ActionAuditChain.ref_only")
        ensure_false(self.l4_writes_event, "L4ActionAuditChain.l4_writes_event")
        ensure_false(self.l4_writes_audit, "L4ActionAuditChain.l4_writes_audit")
        ensure_false(self.stores_evidence, "L4ActionAuditChain.stores_evidence")
        ensure_false(self.verifies_tamper, "L4ActionAuditChain.verifies_tamper")
        ensure_schema_version(self.schema_version, "L4ActionAuditChain.schema_version")

    @property
    def has_required_production_refs(self) -> bool:
        return all(
            ref is not None
            for ref in (
                self.event_ref,
                self.actor_ref,
                self.responsibility_chain_ref,
                self.evidence_ref,
                self.audit_requirement_ref,
                self.provenance_ref,
            )
        )
