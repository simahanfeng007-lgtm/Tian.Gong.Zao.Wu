from l5_phase4_helpers import projection_for_valid
from tiangong_kernel.l5_plugin_host import projection_text_is_safe


def test_public_projection_contains_only_summaries_and_refs():
    projection = projection_for_valid()
    assert projection.lifecycle_summaries
    assert projection.mount_summaries
    assert projection.self_healing_summaries
    serialized_text = repr(projection)
    assert "/tmp/" not in serialized_text
    assert "package.module" not in serialized_text
    assert "token_value" not in serialized_text
    assert all(projection_text_is_safe(summary.summary_text) for summary in projection.lifecycle_summaries + projection.mount_summaries + projection.self_healing_summaries)
