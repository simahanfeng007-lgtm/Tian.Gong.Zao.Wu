from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_direct_file_write():
    report = scan_l6_phase6_text('test:l6_phase6_file_write', 'Path.write_text')
    assert report.passed is False
    assert report.p0_count >= 1
