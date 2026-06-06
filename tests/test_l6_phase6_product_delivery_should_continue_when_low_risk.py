from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_delivery_should_continue_when_low_risk():
    hint = ProductionContinuationHint()
    policy = ProductExecutionFirstPolicy()
    assert hint.continue_when_low_risk is True
    assert policy.produce_candidate_when_low_risk is True
