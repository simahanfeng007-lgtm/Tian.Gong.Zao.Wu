import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_l5_protected_memory_retention_exception():
    score = ForgettingReviewScore(explicit_user_forget_request=1.0, protected_l5_rule_score=0.95)
    assert score.forced_forgetting_review_required is True
    assert score.retention_exception_required is False
    assert score.l5_retention_conflict_review_required is True
    assert score.review_score == 1.0
    state = ForgettingCandidateContinuityState(protected_retention_score=0.95)
    assert state.protected_retention_score >= 0.9
