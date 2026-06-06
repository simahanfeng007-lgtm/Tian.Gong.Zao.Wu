"""Reconciliation advice for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionReconciliationAdvice:
    """Reconciliation advice only; it performs no reconciliation or state write."""

    reconciliation_advice_ref: TypedRef
    action_ref: TypedRef | None = None
    result_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    recovery_requirement_ref: TypedRef | None = None
    advice_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    advice_only: bool = True
    executes_reconciliation: bool = False
    verifies_state: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.advice_items:
            ensure_short_text(key, "ExecutionReconciliationAdvice.advice_items key", 128)
            ensure_short_text(value, "ExecutionReconciliationAdvice.advice_items value")
        ensure_true(self.advice_only, "ExecutionReconciliationAdvice.advice_only")
        ensure_false(self.executes_reconciliation, "ExecutionReconciliationAdvice.executes_reconciliation")
        ensure_false(self.verifies_state, "ExecutionReconciliationAdvice.verifies_state")
        ensure_false(self.writes_l2_state, "ExecutionReconciliationAdvice.writes_l2_state")
        ensure_false(self.writes_audit_store, "ExecutionReconciliationAdvice.writes_audit_store")
        ensure_schema_version(self.schema_version, "ExecutionReconciliationAdvice.schema_version")
