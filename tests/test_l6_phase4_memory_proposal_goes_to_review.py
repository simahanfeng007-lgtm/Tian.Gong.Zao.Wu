import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_memory_proposal_goes_to_review():
    request = MemoryProposalReviewRequest()
    assert request.l3_l5_review_required is True
    assert request.memory_system_review_required is True
    assert request.writes_memory is False
    with pytest.raises(ValueError):
        MemoryProposalReviewRequest(memory_system_review_required=False)
