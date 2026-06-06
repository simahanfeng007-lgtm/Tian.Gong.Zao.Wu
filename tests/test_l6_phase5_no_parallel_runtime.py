import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_parallel_runtime():
    arch = GovernanceControlGroupArchitecture()
    assert arch.issues_permit is False
    assert arch.supports_long_chain_continuation is True
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad_runtime', plugin_kind=GovernancePluginKind.LONG_CHAIN_GOVERNANCE, summary='bad', creates_parallel_runtime=True)
