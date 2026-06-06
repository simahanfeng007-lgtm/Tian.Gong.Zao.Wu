import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_no_direct_budget_charge():
    assert L6Phase3MindQualityGateDecision(no_direct_budget_charge_passed=False).allow_enter_phase4 is False
    assert ResourcePressureProjection().charges_budget is False
    with pytest.raises(ValueError):
        ResourcePressureProjection(charges_budget=True)
