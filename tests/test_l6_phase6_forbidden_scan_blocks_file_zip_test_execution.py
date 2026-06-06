from tiangong_kernel.l6_plugins.product_delivery import *

def test_forbidden_scan_blocks_file_zip_test_execution():
    report = scan_l6_phase6_text('test:l6_phase6_file_zip_test_combo', 'write_product_file\ncreate_zip_now\nrun_tests_now')
    assert report.passed is False
    assert report.p0_count >= 3
