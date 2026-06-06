from tiangong_kernel.l6_plugins.final_closure import L6FinalHandoffEnvelope, L6FinalRiskList

def test_final_handoff_contains_open_risks():
    assert L6FinalHandoffEnvelope().risk_refs
    assert L6FinalRiskList().object_ref == 'report:l6_phase8_final_risk'
