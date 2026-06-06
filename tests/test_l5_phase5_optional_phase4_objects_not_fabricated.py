from tiangong_kernel.l5_plugin_host import PluginSelfHealingDeclaration, PluginRecoveryPlanDeclaration


def test_phase5_consumes_real_phase4_optional_objects_without_refabricating():
    assert PluginSelfHealingDeclaration.__module__.endswith("self_healing_declaration")
    assert PluginRecoveryPlanDeclaration.__module__.endswith("self_healing_declaration")
