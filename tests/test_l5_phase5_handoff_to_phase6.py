from l5_phase5_helpers import valid_audit_index, valid_projection


def test_phase6_consumable_objects_are_summaries_and_refs():
    projection = valid_projection()
    index = valid_audit_index()
    assert projection.handoff_summary
    assert index.boundary_event_refs
