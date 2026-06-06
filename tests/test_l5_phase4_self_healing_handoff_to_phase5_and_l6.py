import tiangong_kernel.l5_plugin_host as l5


def test_self_healing_handoff_objects_are_exported():
    assert "PluginSelfHealingDeclaration" in l5.__all__
    assert "PluginRecoveryPlanDeclaration" in l5.__all__
    assert "PluginSelfHealingValidationReport" in l5.__all__
    assert "PluginSelfHealingQualityGateDecision" in l5.__all__
