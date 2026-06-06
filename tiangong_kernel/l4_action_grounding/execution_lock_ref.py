"""Lock references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionLockRef:
    """Lock reference only; it does not lock files, databases, or threads."""

    lock_ref: TypedRef
    action_ref: TypedRef | None = None
    concurrency_scope_ref: TypedRef | None = None
    lock_hint: str = "lock_ref_only"
    ref_only: bool = True
    creates_real_lock: bool = False
    locks_real_file: bool = False
    locks_database: bool = False
    blocks_real_thread: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.lock_hint, "ExecutionLockRef.lock_hint")
        ensure_true(self.ref_only, "ExecutionLockRef.ref_only")
        ensure_false(self.creates_real_lock, "ExecutionLockRef.creates_real_lock")
        ensure_false(self.locks_real_file, "ExecutionLockRef.locks_real_file")
        ensure_false(self.locks_database, "ExecutionLockRef.locks_database")
        ensure_false(self.blocks_real_thread, "ExecutionLockRef.blocks_real_thread")
        ensure_schema_version(self.schema_version, "ExecutionLockRef.schema_version")
