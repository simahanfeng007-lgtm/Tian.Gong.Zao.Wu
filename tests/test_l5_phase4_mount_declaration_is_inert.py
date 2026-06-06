from dataclasses import FrozenInstanceError
from l5_phase4_helpers import valid_mount
from tiangong_kernel.l5_plugin_host import PluginMountDeclaration, has_forbidden_method


def test_mount_declaration_is_frozen_and_no_execution_method():
    mount = valid_mount()
    assert isinstance(mount, PluginMountDeclaration)
    assert has_forbidden_method(PluginMountDeclaration) == ()
    try:
        mount.mount_point_ref = "changed"
        assert False
    except FrozenInstanceError:
        assert True


def test_mount_declaration_has_no_skill_tool_model_visible_entry():
    mount = valid_mount()
    for forbidden in ("skill_id", "tool_name", "tool_schema", "model_visible_name", "function_schema", "tool_release_ref", "capability_surface", "execution_endpoint", "handler_name", "callable_ref"):
        assert not hasattr(mount, forbidden)
