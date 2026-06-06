import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import LearningNeedReviewRequest

def test_learning_need_review_not_learning_execution():
    request = LearningNeedReviewRequest()
    assert request.learning_executed is False
    with pytest.raises(ValueError):
        LearningNeedReviewRequest(learning_executed=True)
