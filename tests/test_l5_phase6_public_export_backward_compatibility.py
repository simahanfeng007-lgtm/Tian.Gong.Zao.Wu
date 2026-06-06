from tiangong_kernel import l5_plugin_host as host


def test_public_export_backward_compatibility_keeps_previous_phase_exports():
    for name in (
        "PluginPhase5QualityGateDecision",
        "PluginPhase5PublicProjection",
        "PluginLifecycleStateMachine",
        "PluginRegistrySnapshot",
        "PluginManifestSchema",
        "PluginManifestView",
    ):
        assert name in host.__all__
        assert hasattr(host, name)
