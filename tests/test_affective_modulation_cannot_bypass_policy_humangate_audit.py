from tiangong_kernel.l5_plugin_host import AffectiveSafetyBoundaryRef, L5L6HandoffFreeze


def test_affective_modulation_cannot_bypass_policy_humangate_audit():
    safety = AffectiveSafetyBoundaryRef()
    refs = set(safety.forbidden_misuse_refs)
    assert "forbid:affective_policy_bypass" in refs
    assert "forbid:affective_human_gate_bypass" in refs
    assert "forbid:affective_audit_bypass" in refs
    assert safety.no_risk_decision_override_ref
    assert safety.no_budget_override_ref


def test_final_l6_handoff_contains_affective_governance_bypass_forbidden_refs():
    handoff = L5L6HandoffFreeze()
    refs = set(handoff.l6_forbidden_misuse_refs)
    assert "forbid:affective_policy_bypass" in refs
    assert "forbid:affective_human_gate_bypass" in refs
    assert "forbid:affective_audit_bypass" in refs
    assert "forbid:affective_state_as_confirmation_ticket" in refs
