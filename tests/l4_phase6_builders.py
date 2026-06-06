from l3_phase1_builders import typed
from tiangong_kernel.l4_action_grounding import (
    ActionFailureReturnEnvelope,
    ActionResultReturnEnvelope,
    BoundaryFeedbackRef,
    ExecutionAuditRef,
    ExecutionCancellationRequest,
    ExecutionCancellationResult,
    ExecutionCancellationStatus,
    ExecutionEvidenceRef,
    ExecutionObservationRef,
    ExecutionResourceUsage,
    ExecutionResumeRef,
    ExecutionRetryAdviceRef,
    ExecutionRollbackHintRef,
    ExecutionTimeoutFailure,
    ExecutionTimeoutPolicyRef,
    ExecutionTraceRef,
    FailureCategory,
    FailureRecoverabilityHint,
    FailureSeverity,
    L3ReplanSuggestionRef,
    ObservationReturnEnvelope,
    RecoveryRequirementRef,
)


def phase6_ref(offset: int, ref_type: str):
    return typed(9000 + offset, ref_type)


def action_ref():
    return phase6_ref(1, "action")


def observation_ref():
    return ExecutionObservationRef(
        observation_ref=phase6_ref(2, "execution_observation"),
        action_ref=action_ref(),
        summary_ref=phase6_ref(3, "observation_summary"),
    )


def evidence_ref():
    return ExecutionEvidenceRef(
        evidence_ref=phase6_ref(4, "execution_evidence"),
        action_ref=action_ref(),
    )


def audit_ref():
    return ExecutionAuditRef(
        audit_ref=phase6_ref(5, "execution_audit"),
        action_ref=action_ref(),
        audit_requirement_ref=phase6_ref(6, "audit_requirement"),
    )


def trace_ref():
    return ExecutionTraceRef(
        trace_ref=phase6_ref(7, "execution_trace"),
        action_ref=action_ref(),
    )


def resource_usage():
    return ExecutionResourceUsage(
        resource_usage_ref=phase6_ref(8, "execution_resource_usage"),
        action_ref=action_ref(),
        tokens_hint_ref=phase6_ref(9, "tokens_hint"),
        time_ms_hint_ref=phase6_ref(10, "time_ms_hint"),
        bytes_hint_ref=phase6_ref(11, "bytes_hint"),
        adapter_usage_hint_ref=phase6_ref(12, "adapter_usage_hint"),
        process_hint_ref=phase6_ref(13, "process_hint"),
        network_hint_ref=phase6_ref(14, "network_hint"),
        usage_items=(("tokens", "hint_ref"), ("network", "hint_ref")),
    )


def result_return():
    return ActionResultReturnEnvelope(
        outcome_ref=phase6_ref(20, "action_outcome"),
        action_ref=action_ref(),
        result_ref=phase6_ref(21, "action_result"),
        observation_ref=observation_ref().observation_ref,
        evidence_ref=evidence_ref().evidence_ref,
        audit_requirement_ref=audit_ref().audit_requirement_ref,
        resource_usage=resource_usage(),
        trace_ref=trace_ref().trace_ref,
        state_update_suggestion_ref=phase6_ref(22, "state_update_suggestion"),
        result_items=(("result", "ref_only"),),
    )


def retry_advice():
    return ExecutionRetryAdviceRef(
        retry_advice_ref=phase6_ref(30, "retry_advice"),
        action_ref=action_ref(),
        failure_ref=phase6_ref(31, "failure"),
        retry_cost_score_ref=phase6_ref(32, "retry_cost_score"),
    )


def resume_ref():
    return ExecutionResumeRef(
        resume_ref=phase6_ref(33, "resume"),
        action_ref=action_ref(),
        step_ref=phase6_ref(34, "execution_step"),
    )


def rollback_hint():
    return ExecutionRollbackHintRef(
        rollback_hint_ref=phase6_ref(35, "rollback_hint"),
        action_ref=action_ref(),
        failure_ref=phase6_ref(31, "failure"),
        conservative_hint_ref=phase6_ref(36, "conservative_hint"),
    )


def replan_suggestion():
    return L3ReplanSuggestionRef(
        replan_suggestion_ref=phase6_ref(37, "l3_replan_suggestion"),
        action_ref=action_ref(),
        failure_ref=phase6_ref(31, "failure"),
        reason_ref=phase6_ref(38, "replan_reason"),
    )


def failure_return():
    return ActionFailureReturnEnvelope(
        failure_return_ref=phase6_ref(40, "failure_return"),
        action_ref=action_ref(),
        failure_ref=phase6_ref(31, "failure"),
        failure_category=FailureCategory.TIMEOUT,
        failure_severity=FailureSeverity.RECOVERABLE,
        recoverability_hint=FailureRecoverabilityHint.REPLAN_RECOMMENDED,
        retry_advice_ref=retry_advice().retry_advice_ref,
        resume_ref=resume_ref().resume_ref,
        rollback_hint_ref=rollback_hint().rollback_hint_ref,
        replan_suggestion_ref=replan_suggestion().replan_suggestion_ref,
        audit_requirement_ref=audit_ref().audit_requirement_ref,
        trace_ref=trace_ref().trace_ref,
        failure_items=(("failure", "ref_only"),),
    )


def observation_return():
    obs = observation_ref()
    return ObservationReturnEnvelope(
        observation_return_ref=phase6_ref(50, "observation_return"),
        action_ref=action_ref(),
        observation_ref=obs.observation_ref,
        summary_ref=obs.summary_ref,
        evidence_ref=evidence_ref().evidence_ref,
        trace_ref=trace_ref().trace_ref,
    )


def cancellation_request():
    return ExecutionCancellationRequest(
        cancellation_ref=phase6_ref(60, "cancellation"),
        action_ref=action_ref(),
        reason_ref=phase6_ref(61, "cancellation_reason"),
        trace_ref=trace_ref().trace_ref,
    )


def cancellation_result():
    request = cancellation_request()
    return ExecutionCancellationResult(
        cancellation_result_ref=phase6_ref(62, "cancellation_result"),
        cancellation_ref=request.cancellation_ref,
        action_ref=request.action_ref,
        status=ExecutionCancellationStatus.REQUIRES_L5,
        recovery_requirement_ref=phase6_ref(63, "recovery_requirement"),
        trace_ref=request.trace_ref,
    )


def timeout_policy():
    return ExecutionTimeoutPolicyRef(
        timeout_policy_ref=phase6_ref(70, "timeout_policy"),
        action_ref=action_ref(),
        resource_budget_ref=phase6_ref(71, "resource_budget"),
    )


def timeout_failure():
    policy = timeout_policy()
    return ExecutionTimeoutFailure(
        timeout_failure_ref=phase6_ref(72, "timeout_failure"),
        action_ref=action_ref(),
        timeout_policy_ref=policy.timeout_policy_ref,
        elapsed_hint_ref=phase6_ref(73, "elapsed_hint"),
        replan_suggestion_ref=replan_suggestion().replan_suggestion_ref,
        trace_ref=trace_ref().trace_ref,
    )


def boundary_feedback():
    return BoundaryFeedbackRef(
        boundary_feedback_ref=phase6_ref(80, "boundary_feedback"),
        action_ref=action_ref(),
        permit_consumption_summary_ref=phase6_ref(81, "permit_consumption_summary"),
        audit_requirement_ref=audit_ref().audit_requirement_ref,
        confirmation_advice_ref=phase6_ref(82, "confirmation_advice"),
        feedback_items=(("scope", "mismatch_ref_only"),),
    )


def recovery_requirement():
    return RecoveryRequirementRef(
        recovery_requirement_ref=phase6_ref(90, "recovery_requirement"),
        action_ref=action_ref(),
        failure_ref=phase6_ref(31, "failure"),
        validation_requirement_ref=phase6_ref(91, "validation_requirement"),
        requirement_items=(("recovery", "future_l6_requirement_ref"),),
    )
