"""File action result envelopes for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class FileActionResult:
    """Standard file action result; output is by reference only."""

    result_ref: TypedRef
    request_ref: TypedRef
    output_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    side_effect_summary: str = "none"
    resource_usage_summary: str = "none"
    audit_requirement_ref: TypedRef | None = None
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    dry_run_only: bool = False
    fake_result: bool = False
    no_op_result: bool = False
    real_file_read: bool = False
    real_file_mutation: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    result_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.side_effect_summary, "FileActionResult.side_effect_summary")
        ensure_short_text(self.resource_usage_summary, "FileActionResult.resource_usage_summary")
        for key, value in self.payload_items:
            ensure_short_text(key, "FileActionResult.payload_items key", 128)
            ensure_short_text(value, "FileActionResult.payload_items value")
        ensure_false(self.real_file_read, "FileActionResult.real_file_read")
        ensure_false(self.real_file_mutation, "FileActionResult.real_file_mutation")
        ensure_false(self.writes_l2_state, "FileActionResult.writes_l2_state")
        ensure_false(self.writes_audit_store, "FileActionResult.writes_audit_store")
        ensure_true(self.result_envelope_only, "FileActionResult.result_envelope_only")
        ensure_schema_version(self.schema_version, "FileActionResult.schema_version")
