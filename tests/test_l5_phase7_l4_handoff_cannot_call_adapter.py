import pytest
from tiangong_kernel.l5_plugin_host import PluginL4AdapterHandoffDeclaration, has_forbidden_phase7_method


def test_l4_handoff_cannot_call_adapter_or_hold_instance():
    h = PluginL4AdapterHandoffDeclaration()
    assert h.no_direct_adapter_call_ref
    assert h.no_live_external_action_ref
    assert not has_forbidden_phase7_method(h)


def test_l4_handoff_rejects_live_url_locator():
    with pytest.raises(ValueError):
        PluginL4AdapterHandoffDeclaration(adapter_boundary_refs=("http://adapter.local",))
