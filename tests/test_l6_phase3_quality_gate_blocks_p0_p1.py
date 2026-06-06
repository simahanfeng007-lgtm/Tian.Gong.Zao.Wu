import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_quality_gate_blocks_p0_p1_and_hard_invariants():
    assert L6Phase3MindQualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase4 is True
    assert L6Phase3MindQualityGateDecision(p0_count=1).allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(p1_count=1).allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(mind_plugin_is_not_runtime_passed=False).allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(fatigue_projection_not_refusal_authority_passed=False).allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(forbidden_scan_passed=False).allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(public_projection_safety_passed=False).allow_enter_phase4 is False
