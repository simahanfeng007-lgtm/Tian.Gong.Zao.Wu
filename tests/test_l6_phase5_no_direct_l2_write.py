import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_direct_l2_write_declared():
    assert GovernanceReviewRequest().final_decision is False
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad_l2', plugin_kind=GovernancePluginKind.GOVERNANCE_REVIEW, summary='bad', writes_l2_fact=True)
