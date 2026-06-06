import pytest

from l4_phase8_builders import (
    l5_audit_summary,
    l5_boundary_feedback,
    l5_concurrency_summary,
    l5_handoff,
    l5_permit_consumption,
    l5_resource_summary,
    phase8_ref,
)
from tiangong_kernel.l4_execution import (
    L4ToL5BoundaryFeedback,
    L4ToL5ExecutionAuditSummary,
    L4ToL5HandoffEnvelope,
    L4ToL5PermitConsumptionSummary,
    L4ToL5ResourceBudgetSummary,
)


def test_l4_phase8_l4_to_l5_handoff_is_frozen_and_non_decisional():
    handoff = l5_handoff()
    audit = l5_audit_summary()
    feedback = l5_boundary_feedback()
    permit = l5_permit_consumption()
    resource = l5_resource_summary()
    concurrency = l5_concurrency_summary()

    assert "permit" in handoff.required_l5_surfaces
    assert "credential" in handoff.required_l5_surfaces
    assert handoff.implements_l5 is False
    assert handoff.grants_permission is False
    assert handoff.emits_plain_credential is False
    assert audit.writes_audit_store is False
    assert audit.stores_evidence is False
    assert feedback.makes_boundary_decision is False
    assert feedback.generates_confirmation_ticket is False
    assert permit.deducts_real_permit is False
    assert permit.issues_permit is False
    assert resource.implements_resource_policy is False
    assert resource.allocates_resource is False
    assert concurrency.implements_concurrency_policy is False
    assert concurrency.schedules_threads is False
    assert concurrency.creates_real_lock is False


def test_l4_phase8_l4_to_l5_handoff_rejects_l5_implementation_flags():
    with pytest.raises(ValueError):
        L4ToL5HandoffEnvelope(handoff_ref=phase8_ref(180, "handoff"), grants_permission=True)
    with pytest.raises(ValueError):
        L4ToL5ExecutionAuditSummary(audit_summary_ref=phase8_ref(181, "audit_summary"), writes_audit_store=True)
    with pytest.raises(ValueError):
        L4ToL5BoundaryFeedback(feedback_ref=phase8_ref(182, "feedback"), makes_boundary_decision=True)
    with pytest.raises(ValueError):
        L4ToL5PermitConsumptionSummary(permit_consumption_summary_ref=phase8_ref(183, "permit_summary"), issues_permit=True)
    with pytest.raises(ValueError):
        L4ToL5ResourceBudgetSummary(resource_budget_summary_ref=phase8_ref(184, "resource_summary"), allocates_resource=True)
