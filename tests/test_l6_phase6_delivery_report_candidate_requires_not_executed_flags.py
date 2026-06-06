from tiangong_kernel.l6_plugins.product_delivery import *

def test_delivery_report_candidate_requires_not_executed_flags():
    report = DeliveryReportCandidate()
    assert report.not_executed is True
    assert len(report.not_executed_flags) >= 3
