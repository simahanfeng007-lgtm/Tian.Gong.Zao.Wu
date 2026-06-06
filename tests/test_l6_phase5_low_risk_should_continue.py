import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_low_risk_should_continue():
    hint = LongChainContinuationHint()
    assert hint.low_risk_should_continue is True
    assert hint.should_continue_when_safe is True
    with pytest.raises(ValueError):
        LongChainContinuationHint(low_risk_should_continue=False)
