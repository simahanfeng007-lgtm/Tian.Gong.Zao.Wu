"""Resource budget references for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ResourceBudgetRef:
    """Future L5 resource budget reference; L4 allocates no resource budget."""

    resource_budget_ref: TypedRef
    action_ref: TypedRef | None = None
    permit_ref: TypedRef | None = None
    budget_hint: str = "future_l5_resource_budget_ref"
    ref_only: bool = True
    allocates_real_resource: bool = False
    extends_budget: bool = False
    deducts_budget: bool = False
    issues_budget: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.budget_hint, "ResourceBudgetRef.budget_hint")
        ensure_true(self.ref_only, "ResourceBudgetRef.ref_only")
        ensure_false(self.allocates_real_resource, "ResourceBudgetRef.allocates_real_resource")
        ensure_false(self.extends_budget, "ResourceBudgetRef.extends_budget")
        ensure_false(self.deducts_budget, "ResourceBudgetRef.deducts_budget")
        ensure_false(self.issues_budget, "ResourceBudgetRef.issues_budget")
        ensure_schema_version(self.schema_version, "ResourceBudgetRef.schema_version")
