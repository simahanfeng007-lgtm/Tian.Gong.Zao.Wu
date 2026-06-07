"""Resource budget consumption summaries for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ResourceBudgetConsumptionSummary:
    """Budget consumption summary; it deducts no real quota."""

    consumption_summary_ref: TypedRef
    resource_budget_ref: TypedRef
    usage_report_ref: TypedRef | None = None
    budget_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    deducts_real_quota: bool = False
    extends_budget: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.budget_items:
            ensure_short_text(key, "ResourceBudgetConsumptionSummary.budget_items key", 128)
            ensure_short_text(value, "ResourceBudgetConsumptionSummary.budget_items value")
        ensure_true(self.summary_only, "ResourceBudgetConsumptionSummary.summary_only")
        ensure_false(self.deducts_real_quota, "ResourceBudgetConsumptionSummary.deducts_real_quota")
        ensure_false(self.extends_budget, "ResourceBudgetConsumptionSummary.extends_budget")
        ensure_false(self.writes_audit_store, "ResourceBudgetConsumptionSummary.writes_audit_store")
        ensure_schema_version(self.schema_version, "ResourceBudgetConsumptionSummary.schema_version")
