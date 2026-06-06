from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_direct_test_execution():
    report = scan_l6_phase6_text('test:l6_phase6_test_execution', 'pytest.main')
    assert report.passed is False
    assert report.p0_count >= 1
