import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_full_pytest_flag_is_boolean_and_required_for_allow_enter_phase4():
    gate = L6Phase3MindQualityGateDecision(full_pytest_passed_for_freeze=False)
    assert gate.full_pytest_passed_for_freeze is False
    assert gate.allow_enter_phase4 is False
    assert gate.allow_planning_continuation is True
    frozen_gate = L6Phase3MindQualityGateDecision(full_pytest_passed_for_freeze=True)
    assert frozen_gate.allow_enter_phase4 is True
    with pytest.raises(ValueError):
        L6Phase3MindQualityGateDecision(full_pytest_passed_for_freeze="passed")
