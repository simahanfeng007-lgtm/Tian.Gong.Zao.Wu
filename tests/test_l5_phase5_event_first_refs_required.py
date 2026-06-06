from l5_phase5_helpers import valid_audit_index


def test_event_first_refs_cover_all_boundary_types():
    index = valid_audit_index()
    assert index.isolation_event_refs
    assert index.dependency_event_refs
    assert index.credential_event_refs
    assert index.data_governance_event_refs
    assert index.resource_boundary_event_refs
    assert index.switch_boundary_event_refs
    assert index.capability_token_event_refs
    assert index.trust_boundary_event_refs
