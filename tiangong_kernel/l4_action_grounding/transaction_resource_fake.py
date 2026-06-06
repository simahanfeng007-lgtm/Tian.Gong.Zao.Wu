"""Fake transaction/resource support for L4 phase 7 tests."""

from __future__ import annotations

from dataclasses import dataclass

from .adapter_failure import new_adapter_typed_ref
from .execution_commit_intent import ExecutionCommitIntent
from .execution_replay_summary import ExecutionReplaySummary
from .execution_rollback_intent import ExecutionRollbackIntent
from .execution_transaction_ref import ExecutionTransactionRef
from .resource_budget_consumption_summary import ResourceBudgetConsumptionSummary
from .resource_budget_ref import ResourceBudgetRef
from .resource_usage_report import ResourceUsageReport


@dataclass(frozen=True, slots=True)
class FakeTransactionResourceSupport:
    """Test-only support that returns refs and summaries without side effects."""

    test_only: bool = True

    def transaction_ref(self, action_ref) -> ExecutionTransactionRef:
        return ExecutionTransactionRef(transaction_ref=new_adapter_typed_ref("execution_transaction"), action_ref=action_ref)

    def commit_intent(self, transaction_ref, action_ref) -> ExecutionCommitIntent:
        return ExecutionCommitIntent(
            commit_intent_ref=new_adapter_typed_ref("execution_commit_intent"),
            transaction_ref=transaction_ref,
            action_ref=action_ref,
        )

    def rollback_intent(self, transaction_ref, action_ref) -> ExecutionRollbackIntent:
        return ExecutionRollbackIntent(
            rollback_intent_ref=new_adapter_typed_ref("execution_rollback_intent"),
            transaction_ref=transaction_ref,
            action_ref=action_ref,
        )

    def usage_report(self, action_ref, budget_ref: ResourceBudgetRef) -> ResourceUsageReport:
        return ResourceUsageReport(
            resource_usage_report_ref=new_adapter_typed_ref("resource_usage_report"),
            action_ref=action_ref,
            resource_budget_ref=budget_ref.resource_budget_ref,
            usage_items=(("mode", "fake"),),
        )

    def budget_summary(self, budget_ref: ResourceBudgetRef, usage_report: ResourceUsageReport) -> ResourceBudgetConsumptionSummary:
        return ResourceBudgetConsumptionSummary(
            consumption_summary_ref=new_adapter_typed_ref("budget_consumption_summary"),
            resource_budget_ref=budget_ref.resource_budget_ref,
            usage_report_ref=usage_report.resource_usage_report_ref,
            budget_items=(("mode", "fake"),),
        )

    def replay_summary(self, action_ref) -> ExecutionReplaySummary:
        return ExecutionReplaySummary(
            replay_summary_ref=new_adapter_typed_ref("execution_replay_summary"),
            action_refs=(action_ref,),
            replay_items=(("mode", "fake"),),
        )
