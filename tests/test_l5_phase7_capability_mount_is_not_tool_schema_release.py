import pytest
from tiangong_kernel.l5_plugin_host import PluginCapabilityMountBindingDeclaration


def test_capability_mount_is_not_tool_schema_release():
    c = PluginCapabilityMountBindingDeclaration()
    assert c.no_tool_schema_release_ref
    assert c.no_model_visible_execution_ref


def test_capability_mount_rejects_tool_schema_field_by_locator():
    with pytest.raises(ValueError):
        PluginCapabilityMountBindingDeclaration(capability_metadata_ref="function_schema://bad")
