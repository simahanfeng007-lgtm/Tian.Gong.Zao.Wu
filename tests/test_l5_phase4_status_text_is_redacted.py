from tiangong_kernel.l5_plugin_host import PluginLifecycleProjectionSummary, projection_text_is_safe


def test_projection_text_rejects_paths_and_secret_fields():
    assert not projection_text_is_safe("/tmp/plugin.py")
    assert not projection_text_is_safe("token_value=abc")
    safe = PluginLifecycleProjectionSummary("summary:safe", "lifecycle", "safe declaration summary")
    assert projection_text_is_safe(safe.summary_text)
