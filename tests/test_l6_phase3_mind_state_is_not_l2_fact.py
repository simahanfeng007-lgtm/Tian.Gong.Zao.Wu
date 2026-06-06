import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_mind_state_is_candidate_not_l2_fact_or_authorization():
    state = MindStateEnvelope()
    assert state.is_l2_fact is False
    assert state.is_authorization is False
    assert state.is_execution_plan is False
    assert state.digest
    with pytest.raises(ValueError):
        MindStateEnvelope(is_l2_fact=True)
    with pytest.raises(ValueError):
        MindStateEnvelope(is_authorization=True)
