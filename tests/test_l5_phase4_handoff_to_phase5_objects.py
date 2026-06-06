import tiangong_kernel.l5_plugin_host as l5


def test_phase5_consumable_objects_are_exported():
    expected = {
        "PluginLifecycleStateRef", "PluginLifecycleTransitionRule", "PluginLifecycleStateMachine",
        "PluginMountDeclaration", "PluginMountSurfaceRef", "PluginLifecycleValidationReport",
        "PluginMountDeclarationConflictReport", "PluginLifecycleQualityGateDecision",
        "PluginLifecyclePublicProjection", "PluginLifecycleAuditIndex", "PluginSelfHealingDeclaration",
        "PluginRecoveryPlanDeclaration", "PluginSelfHealingValidationReport", "PluginSelfHealingQualityGateDecision",
    }
    assert expected.issubset(set(l5.__all__))
