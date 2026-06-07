"""Timeout policy references and failures for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .failure_category import FailureCategory
from .failure_recoverability_hint import FailureRecoverabilityHint
from .failure_severity import FailureSeverity
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionTimeoutPolicyRef:
    """Timeout policy reference only; it decides no resource policy."""

    timeout_policy_ref: TypedRef
    action_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    policy_hint: str = "future_l5_timeout_policy"
    ref_only: bool = True
    makes_resource_policy: bool = False
    extends_permit: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.policy_hint, "ExecutionTimeoutPolicyRef.policy_hint", 128)
        ensure_true(self.ref_only, "ExecutionTimeoutPolicyRef.ref_only")
        ensure_false(self.makes_resource_policy, "ExecutionTimeoutPolicyRef.makes_resource_policy")
        ensure_false(self.extends_permit, "ExecutionTimeoutPolicyRef.extends_permit")
        ensure_schema_version(self.schema_version, "ExecutionTimeoutPolicyRef.schema_version")


@dataclass(frozen=True, slots=True)
class ExecutionTimeoutFailure:
    """Standard timeout failure envelope; it performs no cancellation itself."""

    timeout_failure_ref: TypedRef
    action_ref: TypedRef
    timeout_policy_ref: TypedRef
    elapsed_hint_ref: TypedRef | None = None
    failure_category: FailureCategory = FailureCategory.TIMEOUT
    failure_severity: FailureSeverity = FailureSeverity.RECOVERABLE
    recoverability_hint: FailureRecoverabilityHint = FailureRecoverabilityHint.REPLAN_RECOMMENDED
    replan_suggestion_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    failure_only: bool = True
    kills_process: bool = False
    retries_action: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.failure_only, "ExecutionTimeoutFailure.failure_only")
        ensure_false(self.kills_process, "ExecutionTimeoutFailure.kills_process")
        ensure_false(self.retries_action, "ExecutionTimeoutFailure.retries_action")
        ensure_false(self.writes_l2_state, "ExecutionTimeoutFailure.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionTimeoutFailure.schema_version")
