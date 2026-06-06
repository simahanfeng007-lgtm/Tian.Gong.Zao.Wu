import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_risk_projection_is_not_decision():
    risk = RiskProjection(risk_score=0.4)
    assert risk.is_final_decision is False
    assert risk.denies_execution is False
    assert risk.blocks_by_default is False
    assert len(risk.digest) == 64
    with pytest.raises(ValueError):
        RiskProjection(is_final_decision=True)
    with pytest.raises(ValueError):
        RiskProjection(blocks_by_default=True)
