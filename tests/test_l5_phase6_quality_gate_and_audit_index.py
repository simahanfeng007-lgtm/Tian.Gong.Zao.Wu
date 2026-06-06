from l5_phase6_factories import quality_gate, audit_index


def test_quality_gate_hard_derives_allow_enter_phase7():
    assert quality_gate(allow_enter_l5_phase7=False).allow_enter_l5_phase7 is True
    assert quality_gate(p1_count=1, allow_enter_l5_phase7=True).allow_enter_l5_phase7 is False
    assert quality_gate(full_pytest_passed=False, allow_enter_l5_phase7=True).allow_enter_l5_phase7 is False


def test_audit_index_event_first_refs_required():
    obj = audit_index()
    assert obj.health_event_refs
    assert obj.disposition_event_refs
    assert obj.permission_event_refs
    assert obj.quality_gate_event_ref
    assert obj.handoff_event_ref
    assert obj.audit_digest == audit_index().audit_digest
