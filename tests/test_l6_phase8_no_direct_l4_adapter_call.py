import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosurePluginDeclaration, FinalClosurePluginKind

def test_no_direct_l4_adapter_call():
    with pytest.raises(ValueError):
        FinalClosurePluginDeclaration(plugin_ref='l6:bad_l4', plugin_kind=FinalClosurePluginKind.FINAL_HANDOFF, summary='summary:bad', calls_l4_adapter=True)
