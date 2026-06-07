"""L4 to L5 execution audit summary for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5ExecutionAuditSummary:
    """Audit summary only; it writes no audit store."""

    audit_summary_ref: TypedRef
    audit_requirement_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    writes_audit_store: bool = False
    stores_evidence: bool = False
    replaces_l5_audit_system: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.audit_items, "L4ToL5ExecutionAuditSummary.audit_items")
        ensure_true(self.summary_only, "L4ToL5ExecutionAuditSummary.summary_only")
        ensure_false(self.writes_audit_store, "L4ToL5ExecutionAuditSummary.writes_audit_store")
        ensure_false(self.stores_evidence, "L4ToL5ExecutionAuditSummary.stores_evidence")
        ensure_false(self.replaces_l5_audit_system, "L4ToL5ExecutionAuditSummary.replaces_l5_audit_system")
        ensure_schema_version(self.schema_version, "L4ToL5ExecutionAuditSummary.schema_version")
