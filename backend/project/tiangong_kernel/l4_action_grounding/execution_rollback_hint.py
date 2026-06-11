"""Rollback hint references for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionRollbackHintRef:
    """Rollback hint reference only; it performs no rollback."""

    rollback_hint_ref: TypedRef
    action_ref: TypedRef
    failure_ref: TypedRef | None = None
    conservative_hint_ref: TypedRef | None = None
    hint_summary: str = "rollback_hint_ref_only"
    ref_only: bool = True
    executes_rollback: bool = False
    restores_file: bool = False
    reverses_network_action: bool = False
    restores_desktop: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.hint_summary, "ExecutionRollbackHintRef.hint_summary")
        ensure_true(self.ref_only, "ExecutionRollbackHintRef.ref_only")
        ensure_false(self.executes_rollback, "ExecutionRollbackHintRef.executes_rollback")
        ensure_false(self.restores_file, "ExecutionRollbackHintRef.restores_file")
        ensure_false(self.reverses_network_action, "ExecutionRollbackHintRef.reverses_network_action")
        ensure_false(self.restores_desktop, "ExecutionRollbackHintRef.restores_desktop")
        ensure_false(self.writes_l2_state, "ExecutionRollbackHintRef.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionRollbackHintRef.schema_version")
