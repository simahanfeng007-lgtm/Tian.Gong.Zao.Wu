"""Resource budget failures for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .failure_category import FailureCategory
from .failure_severity import FailureSeverity
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ResourceBudgetExhaustedFailure:
    """Budget exhausted failure; it does not request or bypass quota."""

    failure_ref: TypedRef
    resource_budget_ref: TypedRef
    action_ref: TypedRef | None = None
    failure_category: FailureCategory = FailureCategory.EXTERNAL_ACTION_BLOCKED
    failure_severity: FailureSeverity = FailureSeverity.BLOCKING
    degrade_advice_ref: TypedRef | None = None
    replan_advice_ref: TypedRef | None = None
    pause_advice_ref: TypedRef | None = None
    message: str = "resource budget exhausted"
    failure_only: bool = True
    budget_extension_requested: bool = False
    bypasses_l5_budget: bool = False
    auto_downgrades_real_action: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "ResourceBudgetExhaustedFailure.message")
        ensure_true(self.failure_only, "ResourceBudgetExhaustedFailure.failure_only")
        ensure_false(self.budget_extension_requested, "ResourceBudgetExhaustedFailure.budget_extension_requested")
        ensure_false(self.bypasses_l5_budget, "ResourceBudgetExhaustedFailure.bypasses_l5_budget")
        ensure_false(self.auto_downgrades_real_action, "ResourceBudgetExhaustedFailure.auto_downgrades_real_action")
        ensure_false(self.writes_l2_state, "ResourceBudgetExhaustedFailure.writes_l2_state")
        ensure_schema_version(self.schema_version, "ResourceBudgetExhaustedFailure.schema_version")
