import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_quality_gate_blocks_p0_p1():
    gate = L6Phase4CognitiveContinuityQualityGateDecision()
    assert gate.allow_enter_phase5 is False
    assert gate.allow_planning_continuation is True
    assert L6Phase4CognitiveContinuityQualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase5 is True
    assert L6Phase4CognitiveContinuityQualityGateDecision(p0_count=1).allow_enter_phase5 is False
    assert L6Phase4CognitiveContinuityQualityGateDecision(p1_count=1).allow_enter_phase5 is False
    assert L6Phase4CognitiveContinuityQualityGateDecision(affective_public_projection_redaction_passed=False).allow_enter_phase5 is False
