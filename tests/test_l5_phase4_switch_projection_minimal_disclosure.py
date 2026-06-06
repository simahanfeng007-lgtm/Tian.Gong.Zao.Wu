from l5_phase4_helpers import projection_for_valid


def test_projection_contains_switch_summaries_without_execution_endpoint():
    projection = projection_for_valid()
    assert projection.switch_readiness_summary_ref
    assert projection.pre_switch_checkpoint_summary_ref
    assert "http://" not in repr(projection)
    assert "package.module" not in repr(projection)
