import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_governance_should_summarize_not_interrupt():
    acc = RiskAccumulationProjection()
    assert acc.stop_by_default is False
    assert acc.summarize_not_interrupt is True
    summary = LongChainGovernanceSummary()
    assert summary.interrupts_by_default is False
    with pytest.raises(ValueError):
        RiskAccumulationProjection(stop_by_default=True)
