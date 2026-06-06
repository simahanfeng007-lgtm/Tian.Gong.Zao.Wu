import pytest

from l4_phase7_builders import action_ref, phase7_ref, transaction_ref, transaction_scope
from tiangong_kernel.l4_action_grounding import ExecutionTransactionRef, ExecutionTransactionScope


def test_l4_phase7_transaction_ref_is_not_real_transaction():
    transaction = transaction_ref()
    scope = transaction_scope()

    assert transaction.ref_only is True
    assert transaction.starts_real_transaction is False
    assert transaction.commits_real_transaction is False
    assert transaction.rolls_back_real_transaction is False
    assert transaction.holds_real_connection is False
    assert transaction.locks_real_resource is False
    assert scope.descriptor_only is True
    assert scope.boundary_permission_granted is False
    assert scope.starts_real_transaction is False
    assert scope.writes_l2_state is False


def test_l4_phase7_transaction_ref_rejects_real_transaction_flags():
    with pytest.raises(ValueError):
        ExecutionTransactionRef(transaction_ref=phase7_ref(100, "execution_transaction"), starts_real_transaction=True)
    with pytest.raises(ValueError):
        ExecutionTransactionRef(transaction_ref=phase7_ref(101, "execution_transaction"), commits_real_transaction=True)
    with pytest.raises(ValueError):
        ExecutionTransactionScope(
            transaction_scope_ref=phase7_ref(102, "execution_transaction_scope"),
            action_ref=action_ref(),
            writes_l2_state=True,
        )
