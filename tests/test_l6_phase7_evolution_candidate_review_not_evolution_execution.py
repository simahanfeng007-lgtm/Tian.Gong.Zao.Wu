import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import EvolutionCandidateReviewEnvelope

def test_evolution_candidate_review_not_evolution_execution():
    item = EvolutionCandidateReviewEnvelope()
    assert item.executes_evolution is False
    with pytest.raises(ValueError):
        EvolutionCandidateReviewEnvelope(executes_evolution=True)
