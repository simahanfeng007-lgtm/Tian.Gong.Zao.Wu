from l5_phase4_helpers import projection_for_valid


def test_self_healing_projection_does_not_expose_full_plan_or_patch():
    projection = projection_for_valid()
    text = repr(projection)
    assert "patch" not in text.lower()
    assert "/tmp/" not in text
    assert "token_value" not in text
    assert projection.self_healing_summaries
