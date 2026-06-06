import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_score_not_decision():
    score = CognitiveReentryScore(pollution_risk_score=0.4)
    assert score.score_is_decision is False
    assert score.score_is_authorization is False
    assert 0 <= score.reentry_priority_score <= 1
    assert score.l5_review_recommended is True
    with pytest.raises(ValueError):
        CognitiveReentryScore(score_is_decision=True)
