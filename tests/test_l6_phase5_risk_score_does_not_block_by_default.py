import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_risk_score_does_not_block_by_default():
    risk = RiskProjection(risk_score=0.7)
    assert risk.blocks_by_default is False
    assert risk.continuation_preferred_when_safe is True
    with pytest.raises(ValueError):
        RiskLevelHint(score_is_decision=True)
