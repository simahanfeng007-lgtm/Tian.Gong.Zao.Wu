from l5_phase5_helpers import valid_projection


def test_projection_does_not_disclose_full_declarations():
    projection = valid_projection()
    text = str(projection)
    assert "credential_handle_refs" not in text
    assert "dependency_refs" not in text
    assert "raw manifest" not in text.lower()
