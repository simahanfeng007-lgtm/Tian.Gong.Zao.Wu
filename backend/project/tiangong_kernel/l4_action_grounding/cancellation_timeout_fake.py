"""Fake cancellation and timeout helpers for L4 phase 6 tests."""

from __future__ import annotations

from dataclasses import dataclass

from .adapter_failure import new_adapter_typed_ref
from .execution_cancellation import ExecutionCancellationRequest, ExecutionCancellationResult, ExecutionCancellationStatus
from .execution_timeout import ExecutionTimeoutFailure, ExecutionTimeoutPolicyRef


@dataclass(frozen=True, slots=True)
class FakeCancellationTimeoutHelper:
    """Test helper only; it does not cancel, retry, or recover anything."""

    test_only: bool = True

    def fake_cancel_result(self, request: ExecutionCancellationRequest) -> ExecutionCancellationResult:
        return ExecutionCancellationResult(
            cancellation_result_ref=new_adapter_typed_ref("cancellation_result"),
            cancellation_ref=request.cancellation_ref,
            action_ref=request.action_ref,
            status=ExecutionCancellationStatus.REQUIRES_L5,
            summary="fake cancellation result only",
            kills_process=False,
            progresses_recovery=False,
        )

    def fake_timeout_failure(self, policy: ExecutionTimeoutPolicyRef, action_ref) -> ExecutionTimeoutFailure:
        return ExecutionTimeoutFailure(
            timeout_failure_ref=new_adapter_typed_ref("timeout_failure"),
            action_ref=action_ref,
            timeout_policy_ref=policy.timeout_policy_ref,
            replan_suggestion_ref=new_adapter_typed_ref("replan_suggestion"),
            kills_process=False,
            retries_action=False,
        )
