from tiangong_kernel.l6_plugins.product_delivery import *

def test_full_pytest_not_faked():
    gate = L6Phase6ProductDeliveryQualityGateDecision()
    assert gate.full_pytest_passed_for_freeze is False
    assert gate.allow_enter_phase7 is False
    freeze_gate = L6Phase6ProductDeliveryQualityGateDecision(full_pytest_passed_for_freeze=True)
    assert freeze_gate.allow_enter_phase7 is True
