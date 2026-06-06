from l5_phase3_sample_factory import audit_index


def test_audit_index_stores_event_refs_only():
    index = audit_index()
    event = index.events[0]
    assert event.event_kind == "registry_snapshot_created"
    assert event.trace_ref.startswith("trace:")
    assert index.by_event_kind("registry_snapshot_created") == (event,)
