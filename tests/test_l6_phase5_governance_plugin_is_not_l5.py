import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_governance_plugin_group_is_not_l5():
    arch = GovernanceControlGroupArchitecture()
    assert arch.governance_plugin_is_not_l5 is True
    assert arch.issues_permit is False
    assert arch.supports_long_chain_continuation is True
    assert len(default_governance_control_plugin_declarations()) == len(GovernancePluginKind)
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad', plugin_kind=GovernancePluginKind.RISK_ASSESSMENT, summary='bad', is_l5=True)
