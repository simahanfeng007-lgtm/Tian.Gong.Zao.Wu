"""Snapshot references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionSnapshotRef:
    """Snapshot reference only; it creates no real system snapshot."""

    snapshot_ref: TypedRef
    action_ref: TypedRef | None = None
    checkpoint_ref: TypedRef | None = None
    snapshot_hint: str = "snapshot_ref_only"
    ref_only: bool = True
    creates_real_snapshot: bool = False
    copies_sensitive_content: bool = False
    writes_persistent_storage: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.snapshot_hint, "ExecutionSnapshotRef.snapshot_hint")
        ensure_true(self.ref_only, "ExecutionSnapshotRef.ref_only")
        ensure_false(self.creates_real_snapshot, "ExecutionSnapshotRef.creates_real_snapshot")
        ensure_false(self.copies_sensitive_content, "ExecutionSnapshotRef.copies_sensitive_content")
        ensure_false(self.writes_persistent_storage, "ExecutionSnapshotRef.writes_persistent_storage")
        ensure_false(self.writes_l2_state, "ExecutionSnapshotRef.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionSnapshotRef.schema_version")
