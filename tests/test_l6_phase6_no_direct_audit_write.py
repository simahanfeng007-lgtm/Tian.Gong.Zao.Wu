from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_direct_audit_write():
    report = scan_l6_phase6_text('test:l6_phase6_audit_write', 'write_audit')
    assert report.passed is False
    assert report.p0_count >= 1
