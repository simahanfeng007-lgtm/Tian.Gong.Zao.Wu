import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_belief_world_candidate_not_fact():
    projection = BeliefWorldReviewProjection(world_candidate_strength=0.7)
    assert projection.canonical_state is False
    assert projection.writes_l2_fact is False
    with pytest.raises(ValueError):
        BeliefWorldReviewProjection(canonical_state=True)
