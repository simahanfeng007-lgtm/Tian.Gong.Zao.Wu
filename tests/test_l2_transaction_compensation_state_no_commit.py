import pytest

from l3_phase1_builders import typed
from tiangong_kernel.l2_state import CompensationState, L2StateIdentity, L2StateKind, L2StateStatus, TransactionState


def identity(index: int) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, "transaction_state"), kind=L2StateKind.BOUNDARY)


def test_l2_transaction_compensation_state_never_commits_or_rolls_back():
    transaction = TransactionState(identity(1), L2StateStatus())
    compensation = CompensationState(identity(2), L2StateStatus())
    assert transaction.commit_performed is False
    assert transaction.rollback_performed is False
    assert compensation.compensation_performed is False

    with pytest.raises(ValueError):
        TransactionState(identity(3), L2StateStatus(), commit_performed=True)
    with pytest.raises(ValueError):
        TransactionState(identity(4), L2StateStatus(), rollback_performed=True)
    with pytest.raises(ValueError):
        CompensationState(identity(5), L2StateStatus(), compensation_performed=True)
