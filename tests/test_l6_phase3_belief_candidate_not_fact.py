import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_belief_candidate_and_state_are_not_facts():
    assert BeliefMindState().belief_is_fact is False
    assert BeliefCandidateProjection().belief_is_fact is False
    with pytest.raises(ValueError):
        BeliefMindState(belief_is_fact=True)
    with pytest.raises(ValueError):
        BeliefCandidateProjection(belief_is_fact=True)
    with pytest.raises(ValueError):
        BeliefCandidateProjection(overwrites_user_requirement=True)
