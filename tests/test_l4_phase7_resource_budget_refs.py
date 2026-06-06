import pytest

from l4_phase7_builders import budget_summary, phase7_ref, resource_budget, resource_failure, usage_report
from tiangong_kernel.l4_action_grounding import (
    ResourceBudgetConsumptionSummary,
    ResourceBudgetExhaustedFailure,
    ResourceBudgetRef,
    ResourceUsageReport,
)


def test_l4_phase7_resource_budget_is_reference_only():
    budget = resource_budget()
    usage = usage_report()
    summary = budget_summary()
    failure = resource_failure()

    assert budget.ref_only is True
    assert budget.allocates_real_resource is False
    assert budget.extends_budget is False
    assert budget.deducts_budget is False
    assert budget.issues_budget is False
    assert usage.report_only is True
    assert usage.reads_real_system_resource is False
    assert usage.allocates_real_resource is False
    assert usage.replaces_l5_budget_decision is False
    assert summary.summary_only is True
    assert summary.deducts_real_quota is False
    assert summary.extends_budget is False
    assert summary.writes_audit_store is False
    assert failure.failure_only is True
    assert failure.budget_extension_requested is False
    assert failure.bypasses_l5_budget is False
    assert failure.writes_l2_state is False


def test_l4_phase7_resource_budget_rejects_real_resource_management():
    budget_ref = phase7_ref(120, "resource_budget")
    with pytest.raises(ValueError):
        ResourceBudgetRef(resource_budget_ref=budget_ref, allocates_real_resource=True)
    with pytest.raises(ValueError):
        ResourceUsageReport(resource_usage_report_ref=phase7_ref(121, "resource_usage_report"), reads_real_system_resource=True)
    with pytest.raises(ValueError):
        ResourceBudgetConsumptionSummary(
            consumption_summary_ref=phase7_ref(122, "resource_budget_consumption_summary"),
            resource_budget_ref=budget_ref,
            deducts_real_quota=True,
        )
    with pytest.raises(ValueError):
        ResourceBudgetExhaustedFailure(
            failure_ref=phase7_ref(123, "failure"),
            resource_budget_ref=budget_ref,
            budget_extension_requested=True,
        )
