from l5_phase5_helpers import full_quality_gate, valid_isolation


def test_declaration_carries_not_authorization_ref():
    decl = valid_isolation()
    assert decl.declaration_not_authorization_ref
    assert decl.permission_grant_prohibited_ref
    assert decl.live_action_prohibited_ref


def test_quality_gate_true_is_not_a_permit_object():
    gate = full_quality_gate()
    assert gate.allow_enter_l5_phase6 is True
    assert not hasattr(gate, "permit")
    assert not hasattr(gate, "lease")
