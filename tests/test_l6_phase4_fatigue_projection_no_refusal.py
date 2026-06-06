import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_fatigue_projection_no_refusal():
    projection = FatigueProjection(fatigue_score=0.9)
    assert projection.refusal_authority is False
    assert projection.can_refuse_without_governance is False
    with pytest.raises(ValueError):
        FatigueProjection(refusal_authority=True)
    with pytest.raises(ValueError):
        FatigueProjection(can_refuse_without_governance=True)
