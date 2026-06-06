from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_direct_l4_adapter_call():
    report = scan_l6_phase6_text('test:l6_phase6_l4_adapter', 'L4LiveAdapter')
    assert report.passed is False
    assert report.p0_count >= 1
