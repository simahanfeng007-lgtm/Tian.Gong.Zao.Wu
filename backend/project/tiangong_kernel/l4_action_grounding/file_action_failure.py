"""File action failures for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class FileActionFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    PERMIT_MISSING = "permit_missing"
    PERMIT_SCOPE_MISMATCH = "permit_scope_mismatch"
    PATH_SCOPE_INVALID = "path_scope_invalid"
    READ_BLOCKED = "read_blocked"
    WRITE_BLOCKED = "write_blocked"
    DELETE_BLOCKED = "delete_blocked"
    OVERWRITE_BLOCKED = "overwrite_blocked"
    SENSITIVE_DATA_BLOCKED = "sensitive_data_blocked"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


@dataclass(frozen=True, slots=True)
class FileActionFailure:
    """Standard file action failure; no file system effect is performed."""

    failure_ref: TypedRef
    request_ref: TypedRef
    failure_kind: FileActionFailureKind = FileActionFailureKind.DISABLED_BY_DEFAULT
    message: str = "file action disabled by default"
    blocked_invariant_names: tuple[str, ...] = field(default_factory=tuple)
    boundary_feedback_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    requires_l5_permit: bool = True
    real_file_read: bool = False
    real_file_mutation: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    retryable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "FileActionFailure.message")
        for item in self.blocked_invariant_names:
            ensure_short_text(item, "FileActionFailure.blocked_invariant_names", 128)
        ensure_true(self.requires_l5_permit, "FileActionFailure.requires_l5_permit")
        ensure_false(self.real_file_read, "FileActionFailure.real_file_read")
        ensure_false(self.real_file_mutation, "FileActionFailure.real_file_mutation")
        ensure_false(self.writes_l2_state, "FileActionFailure.writes_l2_state")
        ensure_false(self.writes_audit_store, "FileActionFailure.writes_audit_store")
        ensure_false(self.retryable, "FileActionFailure.retryable")
        ensure_schema_version(self.schema_version, "FileActionFailure.schema_version")
