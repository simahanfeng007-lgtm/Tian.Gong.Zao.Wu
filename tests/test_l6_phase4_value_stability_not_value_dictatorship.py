import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_value_stability_not_value_dictatorship():
    anchor = ValueStabilityAnchorProjection()
    assert anchor.substitutes_safety_policy is False
    assert anchor.value_decision_engine is False
    with pytest.raises(ValueError):
        ValueStabilityAnchorProjection(value_decision_engine=True)
