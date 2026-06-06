import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_score_models_explainable_and_bounded():
    context = ContextContinuityScore(conversation_continuity=0.9, context_gap=0.1)
    memory = MemoryReentryScore(explicit_user_confirmation=1.0, privacy_risk=0.1)
    forgetting = ForgettingReviewScore(explicit_user_forget_request=1.0)
    reentry = CognitiveReentryScore(context_score=context.continuity_score, memory_score=memory.promotion_review_score, forgetting_score=forgetting.review_score)
    for value in (context.continuity_score, memory.promotion_review_score, forgetting.review_score, reentry.reentry_priority_score):
        assert 0 <= value <= 1
    assert context.score_is_decision is False
