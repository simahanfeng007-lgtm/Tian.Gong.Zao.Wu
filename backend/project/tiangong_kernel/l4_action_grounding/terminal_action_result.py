"""Terminal action result envelopes for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class TerminalActionResult:
    """Standard terminal action result; streams are represented by ref."""

    result_ref: TypedRef
    request_ref: TypedRef
    stdout_ref: TypedRef | None = None
    stderr_ref: TypedRef | None = None
    exit_code_ref: TypedRef | None = None
    resource_usage_summary: str = "none"
    audit_requirement_ref: TypedRef | None = None
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    dry_run_only: bool = False
    fake_result: bool = False
    no_op_result: bool = False
    real_command_executed: bool = False
    process_started: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    result_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.resource_usage_summary, "TerminalActionResult.resource_usage_summary")
        for key, value in self.payload_items:
            ensure_short_text(key, "TerminalActionResult.payload_items key", 128)
            ensure_short_text(value, "TerminalActionResult.payload_items value")
        ensure_false(self.real_command_executed, "TerminalActionResult.real_command_executed")
        ensure_false(self.process_started, "TerminalActionResult.process_started")
        ensure_false(self.writes_l2_state, "TerminalActionResult.writes_l2_state")
        ensure_false(self.writes_audit_store, "TerminalActionResult.writes_audit_store")
        ensure_true(self.result_envelope_only, "TerminalActionResult.result_envelope_only")
        ensure_schema_version(self.schema_version, "TerminalActionResult.schema_version")
