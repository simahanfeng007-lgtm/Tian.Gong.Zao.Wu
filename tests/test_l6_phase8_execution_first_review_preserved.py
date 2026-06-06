import pytest
from tiangong_kernel.l6_plugins.final_closure import L6ExecutionFirstClosurePolicy

def test_execution_first_review_preserved():
    policy = L6ExecutionFirstClosurePolicy()
    assert policy.low_risk_should_continue is True
    assert policy.long_chain_should_degrade_not_abort is True
    with pytest.raises(ValueError):
        L6ExecutionFirstClosurePolicy(low_risk_should_continue=False)
