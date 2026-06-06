import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_long_chain_should_degrade_not_abort():
    suggestion = LongChainDegradedContinuationSuggestion()
    assert suggestion.degrade_not_abort is True
    assert suggestion.aborts_task is False
    with pytest.raises(ValueError):
        LongChainDegradedContinuationSuggestion(aborts_task=True)
