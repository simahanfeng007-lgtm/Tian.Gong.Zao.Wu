import pytest

from l4_phase7_builders import determinism_hint, idempotency_hint, phase7_ref, replay_summary
from tiangong_kernel.l4_action_grounding import ExecutionDeterminismHint, ExecutionIdempotencyHint, ExecutionReplaySummary


def test_l4_phase7_replay_summary_contains_no_plain_credential_or_execution():
    replay = replay_summary()
    determinism = determinism_hint()
    idempotency = idempotency_hint()

    assert replay.summary_only is True
    assert replay.executes_replay is False
    assert replay.guarantees_real_replay is False
    assert replay.contains_plain_credential is False
    assert replay.stores_sensitive_plaintext is False
    assert replay.writes_l2_state is False
    assert determinism.hint_only is True
    assert determinism.enforces_determinism is False
    assert determinism.grants_replay_permission is False
    assert idempotency.hint_only is True
    assert idempotency.authorizes_repeat_execution is False
    assert idempotency.grants_replay_permission is False


def test_l4_phase7_replay_and_hint_objects_reject_execution_or_permission_flags():
    with pytest.raises(ValueError):
        ExecutionReplaySummary(replay_summary_ref=phase7_ref(140, "execution_replay_summary"), executes_replay=True)
    with pytest.raises(ValueError):
        ExecutionReplaySummary(
            replay_summary_ref=phase7_ref(141, "execution_replay_summary"),
            contains_plain_credential=True,
        )
    with pytest.raises(ValueError):
        ExecutionDeterminismHint(determinism_hint_ref=phase7_ref(142, "determinism_hint"), grants_replay_permission=True)
    with pytest.raises(ValueError):
        ExecutionIdempotencyHint(idempotency_hint_ref=phase7_ref(143, "idempotency_hint"), authorizes_repeat_execution=True)
