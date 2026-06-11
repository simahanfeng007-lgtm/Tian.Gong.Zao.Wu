"""Placeholder L5 resource budget port for L4 phase 7."""

from __future__ import annotations

from typing import Protocol

from .resource_budget_consumption_summary import ResourceBudgetConsumptionSummary
from .resource_budget_failure import ResourceBudgetExhaustedFailure
from .resource_budget_ref import ResourceBudgetRef


class L5ResourceBudgetPort(Protocol):
    """Protocol placeholder only; L4 implements no resource policy engine."""

    def describe_budget(self, budget_ref: ResourceBudgetRef) -> ResourceBudgetConsumptionSummary | ResourceBudgetExhaustedFailure:
        ...
