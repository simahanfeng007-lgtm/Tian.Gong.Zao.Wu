from l5_phase5_helpers import full_quality_gate


def test_quality_gate_result_has_no_execution_authorization_entities():
    gate = full_quality_gate()
    for name in ("permit", "lease_object", "confirmation_ticket", "credential_grant", "sandbox_grant"):
        assert not hasattr(gate, name)
