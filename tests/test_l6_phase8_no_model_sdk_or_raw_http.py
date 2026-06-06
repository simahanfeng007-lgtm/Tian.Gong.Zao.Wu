import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosurePluginDeclaration, FinalClosurePluginKind

def test_no_model_sdk_or_raw_http():
    with pytest.raises(ValueError):
        FinalClosurePluginDeclaration(plugin_ref='l6:bad_model', plugin_kind=FinalClosurePluginKind.FINAL_HANDOFF, summary='summary:bad', calls_model=True)
