import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_candidate_fact_review_not_l2_write():
    request = CandidateFactReviewRequest()
    assert request.l2_review_required is True
    assert request.writes_l2_fact is False
    with pytest.raises(ValueError):
        CandidateFactReviewRequest(writes_l2_fact=True)
    with pytest.raises(ValueError):
        CandidateFactReviewRequest(l2_review_required=False)
