from tiangong_kernel.l5_plugin_host import PluginL6EntryDeclaration


def test_phase7_no_l6_plugin_implementation():
    entry = PluginL6EntryDeclaration()
    assert entry.implementation_absent_required is True
    assert entry.no_dynamic_load_ref
    assert entry.no_live_invocation_ref
