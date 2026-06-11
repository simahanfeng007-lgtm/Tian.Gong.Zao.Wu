"""L6 handoff contract declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_or_summary_items, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class L6HandoffContract:
    handoff_contract_ref: str = "handoff:l6_handoff_contract"
    upstream_ref: str = "l3:orchestration_or_l5_host_ref"
    downstream_ref: str = "l6:downstream_consumer_ref"
    summary_items: tuple[str, ...] = field(default_factory=tuple)
    input_digest_refs: tuple[str, ...] = field(default_factory=tuple)
    output_digest_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = "responsibility:l6_handoff_responsibility_chain"
    audit_summary_ref: str = "audit:l6_handoff_audit_summary"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    ref_summary_digest_only: bool = True
    transfers_authorization: bool = False
    transfers_credential: bool = False
    transfers_tool_handle: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.handoff_contract_ref, "L6HandoffContract.handoff_contract_ref")
        ensure_ref_text(self.upstream_ref, "L6HandoffContract.upstream_ref")
        ensure_ref_text(self.downstream_ref, "L6HandoffContract.downstream_ref")
        ensure_ref_or_summary_items(self.summary_items, "L6HandoffContract.summary_items")
        ensure_ref_items(self.input_digest_refs, "L6HandoffContract.input_digest_refs")
        ensure_ref_items(self.output_digest_refs, "L6HandoffContract.output_digest_refs")
        ensure_ref_text(self.responsibility_chain_ref, "L6HandoffContract.responsibility_chain_ref")
        ensure_ref_text(self.audit_summary_ref, "L6HandoffContract.audit_summary_ref")
        ensure_ref_items(self.evidence_refs, "L6HandoffContract.evidence_refs")
        if not self.ref_summary_digest_only or self.transfers_authorization or self.transfers_credential or self.transfers_tool_handle:
            raise ValueError("L6 handoff can transfer only refs, summaries, and digests")
        ensure_schema_version(self.schema_version)
