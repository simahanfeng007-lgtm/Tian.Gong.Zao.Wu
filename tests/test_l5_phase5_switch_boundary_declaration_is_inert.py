from l5_phase5_helpers import valid_switch_boundary
from tiangong_kernel.l5_plugin_host import has_forbidden_phase5_method


def test_switch_boundary_declaration_is_inert():
    decl = valid_switch_boundary()
    assert decl.switch_boundary_digest
    assert not has_forbidden_phase5_method(decl)
