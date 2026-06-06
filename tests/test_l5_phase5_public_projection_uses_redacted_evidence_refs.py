from l5_phase5_helpers import valid_projection


def test_projection_uses_redacted_evidence_refs_not_raw_evidence_field():
    projection = valid_projection()
    assert projection.redacted_evidence_refs
    assert not hasattr(projection, "evidence_ref")
