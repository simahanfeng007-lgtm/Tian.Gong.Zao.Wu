from dataclasses import FrozenInstanceError
from l5_phase4_helpers import valid_self_healing
from tiangong_kernel.l5_plugin_host import PluginSelfHealingDeclaration, has_forbidden_method


def test_self_healing_declaration_is_frozen_and_inert():
    decl = valid_self_healing()
    assert isinstance(decl, PluginSelfHealingDeclaration)
    assert has_forbidden_method(PluginSelfHealingDeclaration) == ()
    try:
        decl.failure_ref = "changed"
        assert False
    except FrozenInstanceError:
        assert True
