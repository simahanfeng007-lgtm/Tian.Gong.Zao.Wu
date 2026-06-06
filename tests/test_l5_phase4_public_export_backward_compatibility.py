import tiangong_kernel.l5_plugin_host as l5


def test_phase1_to_phase3_exports_are_preserved_after_phase4_extension():
    expected_old = {"PluginManifestView", "PluginManifestSchema", "PluginRegistrySnapshot", "PluginRegistryDelta", "PluginRegistryPublicProjection"}
    assert expected_old.issubset(set(l5.__all__))
    expected_new = {"PluginLifecycleStateMachine", "PluginMountDeclaration", "PluginSelfHealingDeclaration"}
    assert expected_new.issubset(set(l5.__all__))
