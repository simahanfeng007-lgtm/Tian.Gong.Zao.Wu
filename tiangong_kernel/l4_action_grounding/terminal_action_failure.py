"""Terminal action failures for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class TerminalActionFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    PERMIT_MISSING = "permit_missing"
    COMMAND_SCOPE_MISMATCH = "command_scope_mismatch"
    DANGEROUS_COMMAND_BLOCKED = "dangerous_command_blocked"
    PRIVILEGE_ESCALATION_BLOCKED = "privilege_escalation_blocked"
    TIMEOUT_REF = "timeout_ref"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


@dataclass(frozen=True, slots=True)
class TerminalActionFailure:
    """Standard terminal action failure; no command is executed."""

    failure_ref: TypedRef
    request_ref: TypedRef
    failure_kind: TerminalActionFailureKind = TerminalActionFailureKind.DISABLED_BY_DEFAULT
    message: str = "terminal action disabled by default"
    blocked_invariant_names: tuple[str, ...] = field(default_factory=tuple)
    boundary_feedback_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    requires_l5_permit: bool = True
    real_command_executed: bool = False
    process_started: bool = False
    privilege_escalated: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    retryable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "TerminalActionFailure.message")
        for item in self.blocked_invariant_names:
            ensure_short_text(item, "TerminalActionFailure.blocked_invariant_names", 128)
        ensure_true(self.requires_l5_permit, "TerminalActionFailure.requires_l5_permit")
        ensure_false(self.real_command_executed, "TerminalActionFailure.real_command_executed")
        ensure_false(self.process_started, "TerminalActionFailure.process_started")
        ensure_false(self.privilege_escalated, "TerminalActionFailure.privilege_escalated")
        ensure_false(self.writes_l2_state, "TerminalActionFailure.writes_l2_state")
        ensure_false(self.writes_audit_store, "TerminalActionFailure.writes_audit_store")
        ensure_false(self.retryable, "TerminalActionFailure.retryable")
        ensure_schema_version(self.schema_version, "TerminalActionFailure.schema_version")
