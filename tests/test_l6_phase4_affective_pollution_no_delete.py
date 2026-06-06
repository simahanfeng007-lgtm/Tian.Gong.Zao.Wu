import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_pollution_no_delete():
    projection = AffectivePollutionRiskProjection(pollution_risk_score=0.8)
    assert projection.removal_command is False
    assert projection.value_dictatorship is False
    assert projection.removes_memory is False
    with pytest.raises(ValueError):
        AffectivePollutionRiskProjection(removal_command=True)
