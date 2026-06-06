import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_governance_review_request_ref_only():
    request = GovernanceReviewRequest()
    assert request.ref_only is True
    assert request.final_decision is False
    assert request.dispatches_review is False
    assert request.risk_projection_refs
    with pytest.raises(ValueError):
        GovernanceReviewRequest(final_decision=True)
