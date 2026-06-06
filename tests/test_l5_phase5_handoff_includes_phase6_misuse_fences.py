from l5_phase5_helpers import valid_projection


def test_handoff_misuse_fence_is_represented_in_phase5_projection():
    projection = valid_projection()
    assert projection.handoff_summary
    assert "boundary declarations only" in str(projection.handoff_summary)
