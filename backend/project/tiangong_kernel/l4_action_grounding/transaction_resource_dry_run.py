"""Dry-run transaction/resource support for L4 phase 7 tests."""

from __future__ import annotations

from dataclasses import dataclass

from .adapter_failure import new_adapter_typed_ref
from .execution_reconciliation_advice import ExecutionReconciliationAdvice
from .resource_budget_ref import ResourceBudgetRef
from .resource_usage_report import ResourceUsageReport


@dataclass(frozen=True, slots=True)
class DryRunTransactionResourceSupport:
    """Dry-run support that returns planning summaries only."""

    dry_run_only: bool = True

    def resource_usage_preview(self, action_ref, budget_ref: ResourceBudgetRef) -> ResourceUsageReport:
        return ResourceUsageReport(
            resource_usage_report_ref=new_adapter_typed_ref("resource_usage_report"),
            action_ref=action_ref,
            resource_budget_ref=budget_ref.resource_budget_ref,
            usage_items=(("mode", "dry_run"),),
        )

    def reconciliation_advice(self, action_ref) -> ExecutionReconciliationAdvice:
        return ExecutionReconciliationAdvice(
            reconciliation_advice_ref=new_adapter_typed_ref("reconciliation_advice"),
            action_ref=action_ref,
            advice_items=(("mode", "dry_run"),),
        )
