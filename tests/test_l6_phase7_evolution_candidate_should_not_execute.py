from tiangong_kernel.l6_plugins.adaptive_collaboration import EvolutionCandidateReviewEnvelope

def test_evolution_candidate_should_not_execute():
    assert EvolutionCandidateReviewEnvelope().executes_evolution is False
