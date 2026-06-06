import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_state_is_not_l2_fact():
    state = CognitiveContinuityStateEnvelope()
    assert state.is_l2_fact is False
    assert state.is_memory_record is False
    assert state.is_execution_plan is False
    with pytest.raises(ValueError):
        CognitiveContinuityStateEnvelope(is_l2_fact=True)
