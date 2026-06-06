from tiangong_kernel.l5_plugin_host import PluginPhase6AuditIndex, PluginPhase6PublicProjection, PluginPhase6QualityGateDecision


def test_handoff_to_phase7_exports_core_objects():
    from tiangong_kernel import l5_plugin_host as host
    assert "PluginHealthSignalDeclaration" in host.__all__
    assert "PluginPhase6QualityGateDecision" in host.__all__
    assert PluginPhase6QualityGateDecision.__name__
    assert PluginPhase6PublicProjection.__name__
    assert PluginPhase6AuditIndex.__name__
