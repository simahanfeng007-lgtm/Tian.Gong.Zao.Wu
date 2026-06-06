from tiangong_kernel.l6_plugins.adaptive_collaboration import RepairPlanCandidate

def test_repair_candidate_should_not_patch():
    assert RepairPlanCandidate().patches_code is False
