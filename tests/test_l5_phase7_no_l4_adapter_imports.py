def test_phase7_no_l4_adapter_imports():
    import tiangong_kernel.l5_plugin_host.phase7_boundary_gate as phase7
    assert not any(name.startswith("l4_") for name in phase7.__dict__)
    assert "PluginL4AdapterHandoffDeclaration" in phase7.__dict__
    assert "PluginL4AdapterHandoffDeclaration"  # declaration name only, not adapter import
