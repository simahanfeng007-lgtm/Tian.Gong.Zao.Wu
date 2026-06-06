import pytest
from tiangong_kernel.l6_plugins.final_closure import L6FreezeCandidateDecision

def test_l6_freeze_requires_planner_review():
    decision = L6FreezeCandidateDecision()
    assert decision.planner_review_required is True
    with pytest.raises(ValueError):
        L6FreezeCandidateDecision(planner_review_required=False)
