import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *


def test_context_belief_world_review_objects_are_review_only():
    assert ContextGapReport().context_reentry_required is True
    assert ContextPollutionRiskProjection().raw_context_exposed is False
    assert BeliefReviewEnvelope().fact_write_allowed is False
    assert BeliefConflictReport().overrides_user_request is False
    assert WorldReviewEnvelope().canonical_state_write_allowed is False
    assert WorldConflictReport().l5_policy_review_required is True
    assert WorldStalenessReport().direct_refresh_allowed is False
    assert WorldConstraintReviewProjection().permission_decision_allowed is False
    assert CandidateFactReviewEnvelope().l2_fact_write_allowed is False
    with pytest.raises(ValueError):
        ContextGapReport(prompt_injection_allowed=True)
    with pytest.raises(ValueError):
        BeliefReviewEnvelope(fact_write_allowed=True)
    with pytest.raises(ValueError):
        WorldReviewEnvelope(canonical_state_write_allowed=True)
    with pytest.raises(ValueError):
        CandidateFactReviewEnvelope(l2_fact_write_allowed=True)


def test_memory_forgetting_full_specialist_objects_are_candidate_only():
    assert MemoryContextSafetyProjection().direct_prompt_injection_allowed is False
    assert MemoryUpdateProposalReviewCandidate().writes_memory is False
    assert MemoryConflictReport().auto_resolution_allowed is False
    assert MemoryDecayProjection().direct_demotion_allowed is False
    assert MemoryPollutionRiskProjection().direct_quarantine_allowed is False
    assert MemoryQuarantineSuggestion().direct_removal is False
    assert MemoryCompressionSuggestion().direct_rewrite_allowed is False
    with pytest.raises(ValueError):
        MemoryContextSafetyProjection(direct_prompt_injection_allowed=True)
    with pytest.raises(ValueError):
        MemoryUpdateProposalReviewCandidate(writes_memory=True)
    with pytest.raises(ValueError):
        MemoryQuarantineSuggestion(direct_removal=True)
    with pytest.raises(ValueError):
        MemoryCompressionSuggestion(raw_memory_exposed=True)
