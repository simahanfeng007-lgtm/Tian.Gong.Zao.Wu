from tiangong_kernel.l5_plugin_host import PluginArtifactProductionMountBindingDeclaration, has_forbidden_phase7_method


def test_production_mount_is_declarative_only():
    p = PluginArtifactProductionMountBindingDeclaration()
    assert p.no_live_build_ref
    assert p.no_live_file_generation_ref
    assert p.no_live_delivery_ref
    assert not has_forbidden_phase7_method(p)
