import inspect

from tiangong_kernel.l2_state import RiskDecisionState, RiskDecisionStatus, RiskSeverityLabel
from tests.test_l2_phase4_serialization import build_phase4_objects


FORBIDDEN_METHODS = {
    "score_risk",
    "calculate_risk",
    "decide",
    "allow",
    "deny",
    "requires_confirmation",
}


def test_l2_phase4_risk_decision_records_refs_and_severity_label():
    objects = build_phase4_objects()
    risk = objects["risk"]

    assert risk.decision_status is RiskDecisionStatus.DECISION_OBSERVED
    assert risk.severity_label is RiskSeverityLabel.A5
    assert risk.subject_ref == objects["phase3"]["action_intent"].identity.state_ref
    assert risk.risk_view_ref is not None
    assert risk.decision_ref is not None
    assert risk.policy_state_refs == (objects["policy"].identity.state_ref,)


def test_l2_phase4_risk_decision_has_no_scoring_or_decision_methods():
    method_names = {
        name
        for name, value in inspect.getmembers(RiskDecisionState, inspect.isfunction)
        if not name.startswith("__")
    }
    assert FORBIDDEN_METHODS.isdisjoint(method_names)
