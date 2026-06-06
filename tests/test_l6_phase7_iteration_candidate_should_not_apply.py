from tiangong_kernel.l6_plugins.adaptive_collaboration import SelfIterationProposalCandidate

def test_iteration_candidate_should_not_apply():
    assert SelfIterationProposalCandidate().applies_iteration is False
