import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosurePluginDeclaration, FinalClosurePluginKind

def test_no_tool_shell_file_network_call():
    with pytest.raises(ValueError):
        FinalClosurePluginDeclaration(plugin_ref='l6:bad_tool', plugin_kind=FinalClosurePluginKind.FINAL_HANDOFF, summary='summary:bad', calls_tool=True)
