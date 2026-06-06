import pytest
from tiangong_kernel.l6_plugins.final_closure import FinalClosureArtifactBase, L6UnifiedQualityGateDecision

def test_final_freeze_requires_total_repair_after_planner_review():
    gate = L6UnifiedQualityGateDecision(full_pytest_passed_for_freeze_candidate=True)
    assert gate.allow_final_freeze_after_planner_review_and_repair == 'conditional'
    with pytest.raises(ValueError):
        FinalClosureArtifactBase(final_freeze_claimed=True)
