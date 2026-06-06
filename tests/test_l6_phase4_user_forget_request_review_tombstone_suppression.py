import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_user_forget_request_review_tombstone_suppression():
    score = ForgettingReviewScore(explicit_user_forget_request=1.0, protected_l5_rule_score=0.0)
    request = ForgettingProposalReviewRequest(proposal_refs=("projection:l6_phase4_tombstone_proposal", "projection:l6_phase4_active_recall_suppression"))
    tombstone = TombstoneProposal()
    suppression = ActiveRecallSuppressionProposal()
    assert score.review_score > 0.5
    assert request.deletion_review_required is True
    assert tombstone.direct_removal is False
    assert suppression.direct_memory_change is False
