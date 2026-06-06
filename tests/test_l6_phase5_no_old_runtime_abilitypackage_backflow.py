import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_old_runtime_abilitypackage_backflow_scan():
    report = scan_l6_phase5_text('test:l6_phase5_old_backflow', 'AbilityPackagePort and AbilityPackage')
    assert report.passed is False
    gate = L6Phase5GovernanceQualityGateDecision(full_pytest_passed_for_freeze=True)
    assert gate.no_old_runtime_abilitypackage_backflow_passed is True
