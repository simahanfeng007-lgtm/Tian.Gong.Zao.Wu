"""Audit evidence responsibility chain handoff to L5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5AuditChainHandoff:
    handoff_ref: TypedRef
    event_requirement_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    responsibility_chain_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    tamper_evidence_ref: TypedRef | None = None
    integrity_chain_ref: TypedRef | None = None
    audit_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    handoff_only: bool = field(default=True)
    writes_event: bool = False
    writes_audit: bool = False
    stores_evidence: bool = False
    verifies_integrity: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.audit_items, "L4ToL5AuditChainHandoff.audit_items")
        ensure_true(self.handoff_only, "L4ToL5AuditChainHandoff.handoff_only")
        ensure_false(self.writes_event, "L4ToL5AuditChainHandoff.writes_event")
        ensure_false(self.writes_audit, "L4ToL5AuditChainHandoff.writes_audit")
        ensure_false(self.stores_evidence, "L4ToL5AuditChainHandoff.stores_evidence")
        ensure_false(self.verifies_integrity, "L4ToL5AuditChainHandoff.verifies_integrity")
        ensure_schema_version(self.schema_version, "L4ToL5AuditChainHandoff.schema_version")
