import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import SkillAcquisitionCandidate

def test_skill_candidate_not_registered_skill():
    candidate = SkillAcquisitionCandidate()
    assert candidate.registered_skill is False
    with pytest.raises(ValueError):
        SkillAcquisitionCandidate(registered_skill=True)
