import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_confirmation_should_batch_when_safe():
    policy = MinimalConfirmationPolicy()
    assert policy.batch_safe_confirmations is True
    assert policy.ask_every_step is False
    lc = LongChainMinimalConfirmationPolicy()
    assert lc.defer_low_risk_confirmations is True
    with pytest.raises(ValueError):
        MinimalConfirmationPolicy(ask_every_step=True)
