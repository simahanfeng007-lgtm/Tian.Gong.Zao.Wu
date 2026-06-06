import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_projection_is_not_fact():
    projection = AffectiveProjection()
    assert projection.is_fact is False
    assert projection.writes_l2_fact is False
    with pytest.raises(ValueError):
        AffectiveProjection(is_fact=True)
