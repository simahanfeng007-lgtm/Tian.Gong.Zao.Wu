import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import RepairPlanCandidate

def test_repair_plan_candidate_not_code_patch():
    plan = RepairPlanCandidate()
    assert plan.patches_code is False
    with pytest.raises(ValueError):
        RepairPlanCandidate(patches_code=True)
