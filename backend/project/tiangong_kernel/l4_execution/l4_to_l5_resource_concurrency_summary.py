"""L4 to L5 resource and concurrency summaries for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5ResourceBudgetSummary:
    """Resource budget summary only; it implements no resource policy."""

    resource_budget_summary_ref: TypedRef
    resource_budget_ref: TypedRef | None = None
    usage_report_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    resource_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    implements_resource_policy: bool = False
    allocates_resource: bool = False
    extends_budget: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.resource_items, "L4ToL5ResourceBudgetSummary.resource_items")
        ensure_true(self.summary_only, "L4ToL5ResourceBudgetSummary.summary_only")
        ensure_false(self.implements_resource_policy, "L4ToL5ResourceBudgetSummary.implements_resource_policy")
        ensure_false(self.allocates_resource, "L4ToL5ResourceBudgetSummary.allocates_resource")
        ensure_false(self.extends_budget, "L4ToL5ResourceBudgetSummary.extends_budget")
        ensure_schema_version(self.schema_version, "L4ToL5ResourceBudgetSummary.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL5ConcurrencySummary:
    """Concurrency summary only; it implements no concurrency policy."""

    concurrency_summary_ref: TypedRef
    concurrency_scope_ref: TypedRef | None = None
    isolation_context_ref: TypedRef | None = None
    lock_ref: TypedRef | None = None
    concurrency_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    implements_concurrency_policy: bool = False
    schedules_threads: bool = False
    creates_real_lock: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.concurrency_items, "L4ToL5ConcurrencySummary.concurrency_items")
        ensure_true(self.summary_only, "L4ToL5ConcurrencySummary.summary_only")
        ensure_false(self.implements_concurrency_policy, "L4ToL5ConcurrencySummary.implements_concurrency_policy")
        ensure_false(self.schedules_threads, "L4ToL5ConcurrencySummary.schedules_threads")
        ensure_false(self.creates_real_lock, "L4ToL5ConcurrencySummary.creates_real_lock")
        ensure_schema_version(self.schema_version, "L4ToL5ConcurrencySummary.schema_version")
