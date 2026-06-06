import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import SkillPatchCandidate

def test_skill_patch_candidate_not_skill_write():
    candidate = SkillPatchCandidate()
    assert candidate.writes_skill is False
    with pytest.raises(ValueError):
        SkillPatchCandidate(writes_skill=True)
