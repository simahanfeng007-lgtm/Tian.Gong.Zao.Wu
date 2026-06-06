import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import LongChainAdaptiveRecoveryPlan

def test_long_chain_recovery_not_scheduler_state():
    item = LongChainAdaptiveRecoveryPlan()
    assert item.scheduler_state is False
    with pytest.raises(ValueError):
        LongChainAdaptiveRecoveryPlan(scheduler_state=True)
