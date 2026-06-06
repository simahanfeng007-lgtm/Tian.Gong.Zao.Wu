import pytest

from l4_phase7_builders import action_ref, commit_intent, phase7_ref, rollback_intent, transaction_ref
from tiangong_kernel.l4_action_grounding import ExecutionCommitIntent, ExecutionRollbackIntent


def test_l4_phase7_commit_and_rollback_are_intents_only():
    commit = commit_intent()
    rollback = rollback_intent()

    assert commit.intent_only is True
    assert commit.executes_commit is False
    assert commit.writes_l2_state is False
    assert commit.grants_commit_permission is False
    assert rollback.intent_only is True
    assert rollback.executes_rollback is False
    assert rollback.restores_file is False
    assert rollback.reverses_network_action is False
    assert rollback.restores_desktop is False
    assert rollback.grants_rollback_permission is False
    assert rollback.writes_l2_state is False


def test_l4_phase7_commit_and_rollback_reject_action_flags():
    transaction = transaction_ref()
    with pytest.raises(ValueError):
        ExecutionCommitIntent(
            commit_intent_ref=phase7_ref(110, "execution_commit_intent"),
            transaction_ref=transaction.transaction_ref,
            action_ref=action_ref(),
            executes_commit=True,
        )
    with pytest.raises(ValueError):
        ExecutionRollbackIntent(
            rollback_intent_ref=phase7_ref(111, "execution_rollback_intent"),
            transaction_ref=transaction.transaction_ref,
            action_ref=action_ref(),
            executes_rollback=True,
        )
