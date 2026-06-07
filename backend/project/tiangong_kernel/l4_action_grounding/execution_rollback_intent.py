"""Rollback intent references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionRollbackIntent:
    """Rollback intent only; it performs no rollback or restoration."""

    rollback_intent_ref: TypedRef
    transaction_ref: TypedRef
    action_ref: TypedRef | None = None
    recovery_requirement_ref: TypedRef | None = None
    intent_summary: str = "rollback_intent_ref_only"
    intent_only: bool = True
    executes_rollback: bool = False
    restores_file: bool = False
    reverses_network_action: bool = False
    restores_desktop: bool = False
    grants_rollback_permission: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.intent_summary, "ExecutionRollbackIntent.intent_summary")
        ensure_true(self.intent_only, "ExecutionRollbackIntent.intent_only")
        ensure_false(self.executes_rollback, "ExecutionRollbackIntent.executes_rollback")
        ensure_false(self.restores_file, "ExecutionRollbackIntent.restores_file")
        ensure_false(self.reverses_network_action, "ExecutionRollbackIntent.reverses_network_action")
        ensure_false(self.restores_desktop, "ExecutionRollbackIntent.restores_desktop")
        ensure_false(self.grants_rollback_permission, "ExecutionRollbackIntent.grants_rollback_permission")
        ensure_false(self.writes_l2_state, "ExecutionRollbackIntent.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionRollbackIntent.schema_version")
