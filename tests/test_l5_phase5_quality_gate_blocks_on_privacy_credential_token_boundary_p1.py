from l5_phase5_helpers import full_quality_gate, validate_all, valid_capability_token, valid_data_governance


def test_quality_gate_blocks_on_privacy_or_token_boundary_p1():
    report = validate_all(data_governance_decls=(valid_data_governance(consent_refs=()),), capability_token_decls=(valid_capability_token(token_scope_refs=()),))
    gate = full_quality_gate(report)
    assert gate.p1_count >= 2
    assert gate.allow_enter_l5_phase6 is False
