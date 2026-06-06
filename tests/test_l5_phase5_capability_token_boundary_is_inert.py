from l5_phase5_helpers import valid_capability_token
from tiangong_kernel.l5_plugin_host import has_forbidden_phase5_method


def test_capability_token_boundary_is_inert():
    decl = valid_capability_token()
    assert decl.capability_token_digest
    assert not has_forbidden_phase5_method(decl)
    assert not hasattr(decl, "token_value")
