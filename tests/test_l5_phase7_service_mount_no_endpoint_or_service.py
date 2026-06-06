import pytest
from tiangong_kernel.l5_plugin_host import PluginServiceMountBindingDeclaration


def test_service_mount_no_endpoint_or_service():
    s = PluginServiceMountBindingDeclaration()
    assert s.no_live_service_ref
    assert s.no_endpoint_ref


def test_service_mount_rejects_url():
    with pytest.raises(ValueError):
        PluginServiceMountBindingDeclaration(service_surface_ref="https://service.invalid")
