"""Transaction references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionTransactionRef:
    """Transaction reference only; it does not start, commit, or rollback a transaction."""

    transaction_ref: TypedRef
    action_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    transaction_hint: str = "transaction_ref_only"
    ref_only: bool = True
    starts_real_transaction: bool = False
    commits_real_transaction: bool = False
    rolls_back_real_transaction: bool = False
    holds_real_connection: bool = False
    locks_real_resource: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.transaction_hint, "ExecutionTransactionRef.transaction_hint")
        ensure_true(self.ref_only, "ExecutionTransactionRef.ref_only")
        ensure_false(self.starts_real_transaction, "ExecutionTransactionRef.starts_real_transaction")
        ensure_false(self.commits_real_transaction, "ExecutionTransactionRef.commits_real_transaction")
        ensure_false(self.rolls_back_real_transaction, "ExecutionTransactionRef.rolls_back_real_transaction")
        ensure_false(self.holds_real_connection, "ExecutionTransactionRef.holds_real_connection")
        ensure_false(self.locks_real_resource, "ExecutionTransactionRef.locks_real_resource")
        ensure_schema_version(self.schema_version, "ExecutionTransactionRef.schema_version")
