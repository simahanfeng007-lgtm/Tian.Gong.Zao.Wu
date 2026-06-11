"""Audit references for L4 phase 6 returns."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionAuditRef:
    """Audit reference or requirement only; it writes no audit store."""

    audit_ref: TypedRef
    action_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    audit_hint: str = "audit_requirement_ref_only"
    ref_only: bool = True
    writes_real_audit: bool = False
    writes_audit_store: bool = False
    issues_permit: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.audit_hint, "ExecutionAuditRef.audit_hint", 128)
        ensure_true(self.ref_only, "ExecutionAuditRef.ref_only")
        ensure_false(self.writes_real_audit, "ExecutionAuditRef.writes_real_audit")
        ensure_false(self.writes_audit_store, "ExecutionAuditRef.writes_audit_store")
        ensure_false(self.issues_permit, "ExecutionAuditRef.issues_permit")
        ensure_schema_version(self.schema_version, "ExecutionAuditRef.schema_version")
