import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosurePluginDeclaration, FinalClosurePluginKind

def test_no_plugin_direct_import_call_state_write():
    with pytest.raises(ValueError):
        FinalClosurePluginDeclaration(plugin_ref='l6:bad_direct', plugin_kind=FinalClosurePluginKind.FINAL_HANDOFF, summary='summary:bad', direct_plugin_link=True)
