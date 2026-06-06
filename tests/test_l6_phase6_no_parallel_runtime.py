from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_parallel_runtime():
    report = scan_l6_phase6_text('test:l6_phase6_parallel_runtime', 'parallel_runtime')
    assert report.passed is False
    assert report.p0_count >= 1
