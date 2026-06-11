"""Operational summary for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionOperationalSummary:
    """Operational summary only; it does not operate resources or concurrency."""

    operational_summary_ref: TypedRef
    action_ref: TypedRef | None = None
    transaction_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    concurrency_scope_ref: TypedRef | None = None
    replay_summary_ref: TypedRef | None = None
    summary_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    manages_real_resource: bool = False
    schedules_concurrency: bool = False
    commits_real_transaction: bool = False
    executes_replay: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.summary_items:
            ensure_short_text(key, "ExecutionOperationalSummary.summary_items key", 128)
            ensure_short_text(value, "ExecutionOperationalSummary.summary_items value")
        ensure_true(self.summary_only, "ExecutionOperationalSummary.summary_only")
        ensure_false(self.manages_real_resource, "ExecutionOperationalSummary.manages_real_resource")
        ensure_false(self.schedules_concurrency, "ExecutionOperationalSummary.schedules_concurrency")
        ensure_false(self.commits_real_transaction, "ExecutionOperationalSummary.commits_real_transaction")
        ensure_false(self.executes_replay, "ExecutionOperationalSummary.executes_replay")
        ensure_false(self.writes_l2_state, "ExecutionOperationalSummary.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionOperationalSummary.schema_version")
