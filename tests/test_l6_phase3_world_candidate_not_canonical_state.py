import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_world_candidate_is_not_canonical_state():
    assert WorldMindState().canonical_world_state is False
    assert WorldCandidateProjection().canonical_state is False
    assert CandidateFactProposal().canonical_fact is False
    with pytest.raises(ValueError):
        WorldMindState(canonical_world_state=True)
    with pytest.raises(ValueError):
        WorldCandidateProjection(canonical_state=True)
    with pytest.raises(ValueError):
        CandidateFactProposal(writes_l2_fact=True)
