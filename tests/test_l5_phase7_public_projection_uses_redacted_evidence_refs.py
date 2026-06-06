from l5_phase7_builders import phase7_projection


def test_phase7_projection_uses_redacted_evidence_refs():
    projection = phase7_projection()
    assert projection.redacted_evidence_refs
    assert not hasattr(projection, "evidence_ref")
