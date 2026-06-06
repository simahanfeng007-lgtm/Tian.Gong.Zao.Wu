import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_six_desires_no_action_dispatch():
    vector = SixDesireTendencyVector(curiosity=0.8)
    assert vector.candidate_ranking_only is True
    assert vector.action_dispatch is False
    with pytest.raises(ValueError):
        SixDesireTendencyVector(action_dispatch=True)
