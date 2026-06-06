from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_direct_budget_charge():
    report = scan_l6_phase6_text('test:l6_phase6_budget_charge', 'charge_budget')
    assert report.passed is False
    assert report.p0_count >= 1
