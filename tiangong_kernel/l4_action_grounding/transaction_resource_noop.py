"""No-op transaction/resource support for L4 phase 7 tests."""

from __future__ import annotations

from dataclasses import dataclass

from .adapter_failure import new_adapter_typed_ref
from .execution_replay_summary import ExecutionReplaySummary
from .resource_usage_report import ResourceUsageReport


@dataclass(frozen=True, slots=True)
class NoOpTransactionResourceSupport:
    """No-op support that reports no action and no side effects."""

    no_op_only: bool = True

    def resource_usage_report(self, action_ref) -> ResourceUsageReport:
        return ResourceUsageReport(
            resource_usage_report_ref=new_adapter_typed_ref("resource_usage_report"),
            action_ref=action_ref,
            usage_items=(("mode", "no_op"),),
        )

    def replay_summary(self, action_ref) -> ExecutionReplaySummary:
        return ExecutionReplaySummary(
            replay_summary_ref=new_adapter_typed_ref("execution_replay_summary"),
            action_refs=(action_ref,),
            replay_items=(("mode", "no_op"),),
        )
