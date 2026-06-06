import pytest

from tiangong_kernel.l5_plugin_host import PluginCompatibilityDeclaration


def test_compatibility_declaration_does_not_auto_migrate():
    decl = PluginCompatibilityDeclaration(
        required_l0_l1_l2_l3_l4_l5_ranges=("L0-L5:current",),
        required_port_refs=("port:plugin_host",),
        required_state_refs=("state:plugin",),
        required_handoff_refs=("handoff:l4_to_l5",),
    )
    assert decl.required_port_refs == ("port:plugin_host",)
    with pytest.raises(ValueError):
        PluginCompatibilityDeclaration(auto_migration_executed=True)
