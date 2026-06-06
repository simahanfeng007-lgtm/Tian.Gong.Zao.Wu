import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_forgetting_candidate_not_delete():
    candidate = ForgettingReviewCandidate(forgetting_score=0.8)
    assert candidate.direct_removal is False
    assert candidate.removes_memory is False
    with pytest.raises(ValueError):
        ForgettingReviewCandidate(direct_removal=True)
