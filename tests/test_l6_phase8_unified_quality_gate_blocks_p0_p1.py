from tiangong_kernel.l6_plugins.final_closure import L6UnifiedQualityGateDecision

def test_unified_quality_gate_blocks_p0_p1():
    assert L6UnifiedQualityGateDecision(full_pytest_passed_for_freeze_candidate=True).allow_l6_candidate_freeze is True
    assert L6UnifiedQualityGateDecision(p0_count=1, full_pytest_passed_for_freeze_candidate=True).allow_l6_candidate_freeze is False
    assert L6UnifiedQualityGateDecision(p1_count=1, full_pytest_passed_for_freeze_candidate=True).allow_l6_candidate_freeze is False
