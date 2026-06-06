import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_reversible_candidate_should_continue():
    hint = ReversibilityRiskHint()
    assert hint.reversible is True
    assert hint.continuation_preferred is True
    with pytest.raises(ValueError):
        ReversibilityRiskHint(reversible=True, continuation_preferred=False)
