from tiangong_kernel.l5_plugin_host import PluginArtifactProductionMountBindingDeclaration


def test_production_plugin_mount_is_not_tool_only():
    p = PluginArtifactProductionMountBindingDeclaration()
    assert p.production_plugin_kind_ref == "ProductionPlugin"
    assert "ToolCapability" not in p.artifact_capability_kind_refs
