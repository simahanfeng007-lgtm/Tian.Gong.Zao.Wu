import pytest

from l4_phase6_builders import action_ref, cancellation_request, cancellation_result, phase6_ref, timeout_failure, timeout_policy
from tiangong_kernel.l4_action_grounding import (
    ExecutionCancellationRequest,
    ExecutionCancellationResult,
    ExecutionCancellationStatus,
    ExecutionTimeoutFailure,
    ExecutionTimeoutPolicyRef,
    FakeCancellationTimeoutHelper,
)


def test_l4_phase6_cancellation_and_timeout_are_structural_only():
    cancel_request = cancellation_request()
    cancel_result = cancellation_result()
    policy = timeout_policy()
    failure = timeout_failure()

    assert cancel_request.kills_process is False
    assert cancel_request.terminates_live_action is False
    assert cancel_result.status is ExecutionCancellationStatus.REQUIRES_L5
    assert cancel_result.progresses_recovery is False
    assert policy.makes_resource_policy is False
    assert failure.kills_process is False
    assert failure.retries_action is False


def test_l4_phase6_fake_cancellation_timeout_helper_does_not_act():
    helper = FakeCancellationTimeoutHelper()
    cancel_result = helper.fake_cancel_result(cancellation_request())
    timeout = helper.fake_timeout_failure(timeout_policy(), action_ref())

    assert cancel_result.kills_process is False
    assert cancel_result.progresses_recovery is False
    assert timeout.kills_process is False
    assert timeout.retries_action is False


def test_l4_phase6_cancellation_timeout_reject_live_behavior():
    with pytest.raises(ValueError):
        ExecutionCancellationRequest(cancellation_ref=phase6_ref(130, "cancellation"), action_ref=action_ref(), kills_process=True)
    with pytest.raises(ValueError):
        ExecutionCancellationResult(
            cancellation_result_ref=phase6_ref(131, "cancellation_result"),
            cancellation_ref=phase6_ref(132, "cancellation"),
            action_ref=action_ref(),
            progresses_recovery=True,
        )
    with pytest.raises(ValueError):
        ExecutionTimeoutPolicyRef(timeout_policy_ref=phase6_ref(133, "timeout_policy"), extends_permit=True)
    with pytest.raises(ValueError):
        ExecutionTimeoutFailure(
            timeout_failure_ref=phase6_ref(134, "timeout_failure"),
            action_ref=action_ref(),
            timeout_policy_ref=phase6_ref(135, "timeout_policy"),
            retries_action=True,
        )
