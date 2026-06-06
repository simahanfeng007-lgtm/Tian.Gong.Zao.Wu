import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import L6Phase7AdaptiveCollaborationQualityGateDecision

def test_full_pytest_not_faked():
    gate = L6Phase7AdaptiveCollaborationQualityGateDecision()
    assert gate.full_pytest_passed_for_freeze is False
    assert gate.allow_enter_phase8 is False
    passed = L6Phase7AdaptiveCollaborationQualityGateDecision(full_pytest_passed_for_freeze=True)
    assert passed.allow_enter_phase8 is True
