"""L6 phase2 audit trace and evidence chain declarations.

The objects in this module are inert evidence indexes. They never write audit
records, store evidence blobs, open files, call lower layers, or authorize work.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)


@dataclass(frozen=True, slots=True)
class L6AuditTraceEnvelope:
    audit_trace_ref: str = "audit:l6_phase2_audit_trace"
    trace_ref: str = "ref:l6_phase2_trace"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase2_required",))
    provenance_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase2_provenance",))
    responsibility_chain_ref: str = "responsibility:l6_phase2_chain"
    accountability_ref: str = "responsibility:l6_phase2_accountability"
    tamper_evidence_ref: str = "evidence:l6_phase2_tamper_evidence"
    public_projection_ref: str = "public:l6_phase2_audit_projection"
    writes_audit_record: bool = False
    stores_evidence_blob: bool = False
    authorizes_execution: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_trace_ref, "L6AuditTraceEnvelope.audit_trace_ref")
        ensure_ref_text(self.trace_ref, "L6AuditTraceEnvelope.trace_ref")
        ensure_ref_items(self.evidence_refs, "L6AuditTraceEnvelope.evidence_refs", required=True)
        ensure_ref_items(self.provenance_refs, "L6AuditTraceEnvelope.provenance_refs")
        ensure_ref_text(self.responsibility_chain_ref, "L6AuditTraceEnvelope.responsibility_chain_ref")
        ensure_ref_text(self.accountability_ref, "L6AuditTraceEnvelope.accountability_ref")
        ensure_ref_text(self.tamper_evidence_ref, "L6AuditTraceEnvelope.tamper_evidence_ref")
        ensure_ref_text(self.public_projection_ref, "L6AuditTraceEnvelope.public_projection_ref")
        for field_name in ("writes_audit_record", "stores_evidence_blob", "authorizes_execution"):
            ensure_bool(getattr(self, field_name), f"L6AuditTraceEnvelope.{field_name}")
        if self.writes_audit_record or self.stores_evidence_blob or self.authorizes_execution:
            raise ValueError("L6 audit trace envelope is evidence-only and cannot write audit records or authorize work")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)

    @property
    def evidence_chain_complete(self) -> bool:
        return bool(
            self.evidence_refs
            and self.trace_ref
            and self.responsibility_chain_ref
            and self.accountability_ref
            and self.tamper_evidence_ref
        )
