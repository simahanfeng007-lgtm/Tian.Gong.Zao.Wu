from tiangong_kernel.l6_plugins.product_delivery import *

def test_no_old_runtime_abilitypackage_backflow():
    report = scan_l6_phase6_text('test:l6_phase6_old_backflow', 'AbilityPackagePort')
    assert report.passed is False
    assert report.p0_count >= 1
