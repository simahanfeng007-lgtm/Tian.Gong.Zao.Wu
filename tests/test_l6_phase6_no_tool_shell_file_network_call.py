from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_tool_shell_file_network_call():
    report = scan_l6_phase6_text('test:l6_phase6_tool_shell', 'subprocess\nos.system\nsocket.')
    assert report.passed is False
    assert report.p0_count >= 3
