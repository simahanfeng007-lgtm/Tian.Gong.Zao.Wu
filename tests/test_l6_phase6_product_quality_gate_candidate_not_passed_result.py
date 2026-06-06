import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_quality_gate_candidate_not_passed_result():
    gate = ProductQualityGateCandidate()
    assert gate.claims_passed_result is False
    with pytest.raises(ValueError):
        ProductQualityGateCandidate(claims_passed_result=True)
