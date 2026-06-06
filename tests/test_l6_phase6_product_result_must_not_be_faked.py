import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_result_must_not_be_faked():
    report = TestResultReportCandidate()
    gate = ProductQualityGateCandidate()
    assert report.real_test_result is False
    assert gate.claims_real_test_result is False
    with pytest.raises(ValueError):
        TestResultReportCandidate(real_test_result=True)
