from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_model_sdk_or_raw_http():
    report = scan_l6_phase6_text('test:l6_phase6_model_http', 'import deepseek\nhttpx.\nrequests.')
    assert report.passed is False
    assert report.p0_count >= 3
