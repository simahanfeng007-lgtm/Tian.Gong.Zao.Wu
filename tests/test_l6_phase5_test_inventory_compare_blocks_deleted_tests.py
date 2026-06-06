import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_inventory_compare_contract_blocks_deleted_tests():
    gate = L6Phase5GovernanceQualityGateDecision(test_inventory_compare_passed=True, full_pytest_passed_for_freeze=True)
    assert gate.test_inventory_compare_passed is True
    assert gate.allow_enter_phase6 is True
    bad = L6Phase5GovernanceQualityGateDecision(test_inventory_compare_passed=False, full_pytest_passed_for_freeze=True)
    assert bad.allow_enter_phase6 is False
