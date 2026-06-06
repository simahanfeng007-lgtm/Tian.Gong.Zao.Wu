import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_direct_memory_delete_declared():
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad_memory_delete', plugin_kind=GovernancePluginKind.GOVERNANCE_REVIEW, summary='bad', deletes_memory=True)
