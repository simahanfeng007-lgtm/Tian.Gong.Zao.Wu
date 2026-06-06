import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import SelfIterationProposalCandidate

def test_iteration_proposal_not_iteration_apply():
    item = SelfIterationProposalCandidate()
    assert item.applies_iteration is False
    with pytest.raises(ValueError):
        SelfIterationProposalCandidate(applies_iteration=True)
