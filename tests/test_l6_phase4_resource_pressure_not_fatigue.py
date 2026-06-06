import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_resource_pressure_not_fatigue():
    projection = ResourcePressureProjection(budget_pressure_score=0.8)
    assert projection.is_fatigue is False
    assert projection.charges_budget is False
    with pytest.raises(ValueError):
        ResourcePressureProjection(is_fatigue=True)
    with pytest.raises(ValueError):
        ResourcePressureProjection(charges_budget=True)
