import pytest

from tiangong_kernel.l3_orchestration import (
    AuditFlow,
    DecisionFlow,
    EventAppendFlow,
    ExecutionHandoffFlow,
    HumanApprovalFlow,
    LeaseValidationFlow,
    ObservationFeedbackFlow,
    OrchestrationFlowSpec,
    ScheduleTriggerTimerFlow,
    SkillToolReleaseFlow,
    StateTransitionFlow,
)


def test_l3_run_loop_flow_default_passive_flags_are_true():
    flow = OrchestrationFlowSpec(reason_codes=("passive_flow",))
    assert flow.request_only is True
    assert flow.advisory_only is True
    assert flow.reference_only is True
    assert flow.no_execution is True
    assert flow.no_decision is True
    assert flow.no_persistence is True


@pytest.mark.parametrize(
    "field_name",
    ("request_only", "advisory_only", "reference_only", "no_execution", "no_decision", "no_persistence"),
)
def test_l3_run_loop_flow_rejects_disabled_boundary_flags(field_name):
    with pytest.raises(ValueError):
        OrchestrationFlowSpec(**{field_name: False})


def test_l3_run_loop_flow_rejects_non_lower_snake_reason_codes():
    with pytest.raises(ValueError):
        OrchestrationFlowSpec(reason_codes=("BadReason",))


def test_l3_run_loop_flow_specialized_flows_do_not_perform_reserved_actions():
    with pytest.raises(ValueError):
        LeaseValidationFlow(lease_granted=True)
    with pytest.raises(ValueError):
        EventAppendFlow(event_store_write=True)
    with pytest.raises(ValueError):
        StateTransitionFlow(state_write=True)
    with pytest.raises(ValueError):
        AuditFlow(audit_store_write=True)
    with pytest.raises(ValueError):
        HumanApprovalFlow(confirmation_ticket_issued=True)
    with pytest.raises(ValueError):
        ScheduleTriggerTimerFlow(background_task_started=True)
    assert DecisionFlow().no_decision is True


@pytest.mark.parametrize("flow_cls", (SkillToolReleaseFlow, ExecutionHandoffFlow, ObservationFeedbackFlow))
def test_l3_run_loop_new_specialized_flows_are_refs_only(flow_cls):
    flow = flow_cls()
    assert flow.request_only is True
    assert flow.advisory_only is True
    assert flow.reference_only is True
    assert flow.no_execution is True
    assert flow.no_decision is True
    assert flow.no_persistence is True
