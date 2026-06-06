import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_memory_candidate_not_memory_write():
    candidate = MemoryPromotionReviewCandidate(promotion_score=0.7)
    assert candidate.memory_update_proposal is False
    assert candidate.writes_memory is False
    with pytest.raises(ValueError):
        MemoryPromotionReviewCandidate(memory_update_proposal=True)
