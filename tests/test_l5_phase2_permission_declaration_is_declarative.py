import pytest

from tiangong_kernel.l5_plugin_host import PluginPermissionDeclaration


def test_permission_declares_but_never_issues_permit():
    decl = PluginPermissionDeclaration(
        required_permissions=("permission:read_refs",),
        human_confirmation_required=True,
        lease_required=True,
        policy_refs=("policy:permit",),
    )
    assert not decl.permit_issued
    with pytest.raises(ValueError):
        PluginPermissionDeclaration(permit_issued=True)
