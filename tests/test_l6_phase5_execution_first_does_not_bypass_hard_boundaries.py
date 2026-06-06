import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_execution_first_does_not_bypass_hard_boundaries():
    hint = ExecutionContinuityPriorityHint()
    assert hint.execution_first is True
    assert hint.bypass_hard_boundaries is False
    assert hint.summarizes_not_interrupts is True
    with pytest.raises(ValueError):
        ExecutionContinuityPriorityHint(bypass_hard_boundaries=True)
