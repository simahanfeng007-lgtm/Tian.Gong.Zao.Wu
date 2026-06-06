from dataclasses import FrozenInstanceError
from l5_phase5_helpers import valid_isolation
from tiangong_kernel.l5_plugin_host import has_forbidden_phase5_method


def test_isolation_declaration_is_frozen_and_inert():
    decl = valid_isolation()
    assert decl.isolation_digest
    assert not has_forbidden_phase5_method(decl)
    try:
        decl.isolation_boundary_ref = "changed"
        assert False
    except FrozenInstanceError:
        assert True
