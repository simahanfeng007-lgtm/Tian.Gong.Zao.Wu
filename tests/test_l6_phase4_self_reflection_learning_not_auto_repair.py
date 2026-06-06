import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_self_reflection_learning_not_auto_repair():
    candidate = SelfReflectionLearningCandidate(learning_need_score=0.9)
    assert candidate.auto_repair is False
    assert candidate.auto_migration is False
    with pytest.raises(ValueError):
        SelfReflectionLearningCandidate(auto_repair=True)
    with pytest.raises(ValueError):
        SelfReflectionLearningState(auto_repair_allowed=True)
