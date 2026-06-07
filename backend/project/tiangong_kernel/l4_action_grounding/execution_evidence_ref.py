"""Evidence references for L4 phase 6 returns."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionEvidenceRef:
    """Reference to future evidence; it stores no evidence content."""

    evidence_ref: TypedRef
    action_ref: TypedRef | None = None
    evidence_kind_hint: str = "future_l6_evidence"
    ref_only: bool = True
    stores_real_evidence: bool = False
    copies_sensitive_content: bool = False
    holds_large_text: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.evidence_kind_hint, "ExecutionEvidenceRef.evidence_kind_hint", 128)
        ensure_true(self.ref_only, "ExecutionEvidenceRef.ref_only")
        ensure_false(self.stores_real_evidence, "ExecutionEvidenceRef.stores_real_evidence")
        ensure_false(self.copies_sensitive_content, "ExecutionEvidenceRef.copies_sensitive_content")
        ensure_false(self.holds_large_text, "ExecutionEvidenceRef.holds_large_text")
        ensure_schema_version(self.schema_version, "ExecutionEvidenceRef.schema_version")
