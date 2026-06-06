import pytest
from tiangong_kernel.l5_plugin_host import PluginRouteDeclaration


def test_route_declaration_no_live_dispatch():
    r = PluginRouteDeclaration()
    assert r.no_live_dispatch_ref
    assert r.contract_ref


def test_route_rejects_endpoint_locator():
    with pytest.raises(ValueError):
        PluginRouteDeclaration(route_boundary_ref="https://example.invalid/route")
