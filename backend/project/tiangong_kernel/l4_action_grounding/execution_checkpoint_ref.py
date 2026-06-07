"""Checkpoint references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionCheckpointRef:
    """Checkpoint reference only; it creates no snapshot or persistent state."""

    checkpoint_ref: TypedRef
    action_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    checkpoint_hint: str = "checkpoint_ref_only"
    ref_only: bool = True
    creates_real_checkpoint: bool = False
    saves_real_file: bool = False
    persists_state: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.checkpoint_hint, "ExecutionCheckpointRef.checkpoint_hint")
        ensure_true(self.ref_only, "ExecutionCheckpointRef.ref_only")
        ensure_false(self.creates_real_checkpoint, "ExecutionCheckpointRef.creates_real_checkpoint")
        ensure_false(self.saves_real_file, "ExecutionCheckpointRef.saves_real_file")
        ensure_false(self.persists_state, "ExecutionCheckpointRef.persists_state")
        ensure_false(self.writes_l2_state, "ExecutionCheckpointRef.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionCheckpointRef.schema_version")
