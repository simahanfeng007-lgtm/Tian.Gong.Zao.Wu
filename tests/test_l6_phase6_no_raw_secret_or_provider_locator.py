from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_raw_secret_or_provider_locator():
    report = scan_l6_phase6_text('test:l6_phase6_secret_locator', 'api_key=\nbase_url=')
    assert report.passed is False
    assert report.p0_count >= 2
