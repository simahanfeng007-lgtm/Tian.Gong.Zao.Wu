import pytest

from tiangong_kernel.l3_orchestration import TransactionCompensationFlow


def test_l3_transaction_compensation_flow_is_plan_refs_only():
    flow = TransactionCompensationFlow()
    assert flow.commit_performed is False
    assert flow.rollback_performed is False
    with pytest.raises(ValueError):
        TransactionCompensationFlow(rollback_performed=True)
