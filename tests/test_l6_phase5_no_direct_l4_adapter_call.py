import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_direct_l4_adapter_call_declared():
    for decl in default_governance_control_plugin_declarations():
        assert decl.calls_l4_adapter is False
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad_adapter', plugin_kind=GovernancePluginKind.GOVERNANCE_REVIEW, summary='bad', calls_l4_adapter=True)
