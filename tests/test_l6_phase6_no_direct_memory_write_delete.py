from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_direct_memory_write_delete():
    report = scan_l6_phase6_text('test:l6_phase6_memory_write_delete', 'write_memory\ndelete_memory')
    assert report.passed is False
    assert report.p0_count >= 2
