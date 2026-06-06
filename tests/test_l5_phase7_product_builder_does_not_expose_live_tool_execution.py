import pytest
from tiangong_kernel.l5_plugin_host import PluginArtifactProductionMountBindingDeclaration


def test_product_builder_does_not_expose_live_tool_execution():
    p = PluginArtifactProductionMountBindingDeclaration()
    assert p.no_direct_tool_call_ref
    assert p.no_direct_l4_adapter_ref


def test_product_builder_rejects_call_tool_locator():
    with pytest.raises(ValueError):
        PluginArtifactProductionMountBindingDeclaration(no_direct_tool_call_ref="call_tool:now")
