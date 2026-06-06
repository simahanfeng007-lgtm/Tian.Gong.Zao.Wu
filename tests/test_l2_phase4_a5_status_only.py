from tiangong_kernel.l0_primitives.serialization import stable_json_dumps
from tiangong_kernel.l2_state import RiskDecisionState, RiskDecisionStatus, RiskSeverityLabel
from tests.test_l2_phase4_serialization import identity, status, typed


def test_l2_phase4_a5_is_only_a_recorded_label_not_an_internal_interceptor():
    state = RiskDecisionState(
        identity=identity(700),
        status=status(),
        decision_status=RiskDecisionStatus.RISK_VIEW_OBSERVED,
        severity_label=RiskSeverityLabel.A5,
        subject_ref=typed(701, "tool_intent"),
        risk_view_ref=typed(702, "risk_view"),
    )

    payload = stable_json_dumps(state)
    assert '"severity_label":"a5"' in payload
    assert not hasattr(state, "block")
    assert not hasattr(state, "deny")
    assert not hasattr(state, "allow")
