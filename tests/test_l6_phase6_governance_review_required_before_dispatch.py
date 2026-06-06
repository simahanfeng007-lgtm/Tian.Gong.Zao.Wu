from tiangong_kernel.l6_plugins.product_delivery import *

def test_governance_review_required_before_dispatch():
    intent = ProductExecutionDispatchIntent()
    bridge = ProductGovernanceReviewRequest()
    phase5_request = bridge.to_phase5_request()
    assert intent.governance_review_required is True
    assert bridge.phase5_review_required is True
    assert phase5_request.ref_only is True
    assert phase5_request.final_decision is False
