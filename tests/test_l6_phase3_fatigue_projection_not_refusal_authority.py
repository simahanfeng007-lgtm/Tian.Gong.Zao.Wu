import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_fatigue_projection_is_not_refusal_authority():
    fatigue = FatigueProjection(fatigue_score=0.8)
    assert fatigue.refusal_authority is False
    assert fatigue.fatigue_score == 0.8
    with pytest.raises(ValueError):
        FatigueProjection(refusal_authority=True)
