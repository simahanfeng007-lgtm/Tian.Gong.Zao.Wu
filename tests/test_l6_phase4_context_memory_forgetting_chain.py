import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_context_memory_forgetting_chain_is_candidate_only():
    context = ContextContinuityProjection()
    recall = MemoryRecallReentryCandidate(recall_priority_score=0.8)
    forgetting = ForgettingReviewCandidate(forgetting_score=0.7)
    assert context.causes_side_effect is False
    assert recall.force_recall is False
    assert forgetting.direct_removal is False
