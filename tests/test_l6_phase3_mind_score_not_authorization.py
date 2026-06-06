import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_mind_score_is_not_authorization_or_decision():
    vector = MindScoreVector()
    assert vector.is_authorization is False
    assert vector.is_decision is False
    assert MindFusionScoreModel().weighted_score >= 0
    with pytest.raises(ValueError):
        MindScoreVector(is_authorization=True)
    with pytest.raises(ValueError):
        MindScoreBase(score_is_decision=True)
