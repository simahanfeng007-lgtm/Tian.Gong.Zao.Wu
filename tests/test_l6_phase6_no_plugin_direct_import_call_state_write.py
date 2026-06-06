from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_plugin_direct_import_call_state_write():
    report = scan_l6_phase6_text('test:l6_phase6_plugin_direct', 'plugin_instance\ndirect_event_queue')
    assert report.passed is False
    assert report.p0_count >= 2
