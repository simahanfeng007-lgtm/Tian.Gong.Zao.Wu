import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_phase3_quality_gate_blocks_direct_l4_adapter():
    assert L6Phase3MindQualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase4 is True
    assert L6Phase3MindQualityGateDecision(no_direct_l4_adapter_passed=False).allow_enter_phase4 is False
    with pytest.raises(ValueError):
        MindModelNeed(direct_l4_adapter_access=True)
