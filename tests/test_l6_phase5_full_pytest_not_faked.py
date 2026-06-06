import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_full_pytest_field_is_explicit_not_auto_granted():
    gate = L6Phase5GovernanceQualityGateDecision()
    assert gate.full_pytest_passed_for_freeze is False
    assert gate.allow_enter_phase6 is False
    assert gate.allow_planning_continuation is True
    frozen_gate = L6Phase5GovernanceQualityGateDecision(full_pytest_passed_for_freeze=True)
    assert frozen_gate.full_pytest_passed_for_freeze is True
    assert frozen_gate.allow_enter_phase6 is True
