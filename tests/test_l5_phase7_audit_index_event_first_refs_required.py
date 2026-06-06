from l5_phase7_builders import phase7_audit_index


def test_phase7_audit_index_event_first_refs_required():
    audit = phase7_audit_index()
    assert audit.event_refs
    assert audit.evidence_refs
    assert audit.audit_digest
