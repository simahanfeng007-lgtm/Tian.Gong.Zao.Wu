from l3_phase1_builders import typed
from tiangong_kernel.l4_action_grounding import (
    ConcurrencyScope,
    DeterminismKind,
    ExecutionCheckpointRef,
    ExecutionCommitIntent,
    ExecutionDeterminismHint,
    ExecutionIdempotencyHint,
    ExecutionIsolationContext,
    ExecutionLockRef,
    ExecutionOperationalSummary,
    ExecutionReconciliationAdvice,
    ExecutionReplaySummary,
    ExecutionRollbackIntent,
    ExecutionSideEffectSummary,
    ExecutionSnapshotRef,
    ExecutionTransactionRef,
    ExecutionTransactionScope,
    IdempotencyKind,
    L4ToL5ResourceFeedback,
    L4ToL6RecoveryReplayRequirement,
    ResourceBudgetConsumptionSummary,
    ResourceBudgetExhaustedFailure,
    ResourceBudgetRef,
    ResourceUsageReport,
)


def phase7_ref(offset: int, ref_type: str):
    return typed(10000 + offset, ref_type)


def action_ref():
    return phase7_ref(1, "action")


def transaction_ref():
    return ExecutionTransactionRef(
        transaction_ref=phase7_ref(2, "execution_transaction"),
        action_ref=action_ref(),
        step_ref=phase7_ref(3, "execution_step"),
    )


def transaction_scope():
    return ExecutionTransactionScope(
        transaction_scope_ref=phase7_ref(4, "execution_transaction_scope"),
        action_ref=action_ref(),
        step_ref=phase7_ref(3, "execution_step"),
        tool_group_ref=phase7_ref(5, "tool_group"),
        side_effect_scope_ref=phase7_ref(6, "side_effect_scope"),
        scope_items=(("scope", "ref_only"),),
    )


def commit_intent():
    transaction = transaction_ref()
    return ExecutionCommitIntent(
        commit_intent_ref=phase7_ref(7, "execution_commit_intent"),
        transaction_ref=transaction.transaction_ref,
        action_ref=action_ref(),
    )


def rollback_intent():
    transaction = transaction_ref()
    return ExecutionRollbackIntent(
        rollback_intent_ref=phase7_ref(8, "execution_rollback_intent"),
        transaction_ref=transaction.transaction_ref,
        action_ref=action_ref(),
        recovery_requirement_ref=phase7_ref(9, "recovery_requirement"),
    )


def resource_budget():
    return ResourceBudgetRef(
        resource_budget_ref=phase7_ref(10, "resource_budget"),
        action_ref=action_ref(),
        permit_ref=phase7_ref(11, "permit"),
    )


def usage_report():
    budget = resource_budget()
    return ResourceUsageReport(
        resource_usage_report_ref=phase7_ref(12, "resource_usage_report"),
        action_ref=action_ref(),
        resource_budget_ref=budget.resource_budget_ref,
        token_usage_hint_ref=phase7_ref(13, "token_usage_hint"),
        time_usage_hint_ref=phase7_ref(14, "time_usage_hint"),
        bytes_usage_hint_ref=phase7_ref(15, "bytes_usage_hint"),
        adapter_call_count_hint_ref=phase7_ref(16, "adapter_call_count_hint"),
        external_action_hint_ref=phase7_ref(17, "external_action_hint"),
        process_hint_ref=phase7_ref(18, "process_hint"),
        network_hint_ref=phase7_ref(19, "network_hint"),
        usage_items=(("tokens", "hint_ref"), ("network", "hint_ref")),
    )


def budget_summary():
    budget = resource_budget()
    usage = usage_report()
    return ResourceBudgetConsumptionSummary(
        consumption_summary_ref=phase7_ref(20, "resource_budget_consumption_summary"),
        resource_budget_ref=budget.resource_budget_ref,
        usage_report_ref=usage.resource_usage_report_ref,
        budget_items=(("consumption", "summary_only"),),
    )


def resource_failure():
    budget = resource_budget()
    return ResourceBudgetExhaustedFailure(
        failure_ref=phase7_ref(21, "failure"),
        resource_budget_ref=budget.resource_budget_ref,
        action_ref=action_ref(),
    )


def concurrency_scope():
    return ConcurrencyScope(
        concurrency_scope_ref=phase7_ref(22, "concurrency_scope"),
        run_ref=phase7_ref(23, "run"),
        session_ref=phase7_ref(24, "session"),
        step_ref=phase7_ref(3, "execution_step"),
        adapter_ref=phase7_ref(25, "adapter"),
        tool_group_ref=phase7_ref(5, "tool_group"),
        scope_items=(("lane", "descriptor_only"),),
    )


def isolation_context():
    budget = resource_budget()
    return ExecutionIsolationContext(
        isolation_context_ref=phase7_ref(26, "execution_isolation_context"),
        namespace_ref=phase7_ref(27, "namespace"),
        scope_ref=concurrency_scope().concurrency_scope_ref,
        trace_ref=phase7_ref(28, "execution_trace"),
        resource_budget_ref=budget.resource_budget_ref,
        permit_ref=phase7_ref(11, "permit"),
        isolation_items=(("namespace", "ref_only"),),
    )


def lock_ref():
    return ExecutionLockRef(
        lock_ref=phase7_ref(29, "execution_lock"),
        action_ref=action_ref(),
        concurrency_scope_ref=concurrency_scope().concurrency_scope_ref,
    )


def replay_summary():
    return ExecutionReplaySummary(
        replay_summary_ref=phase7_ref(30, "execution_replay_summary"),
        action_refs=(action_ref(),),
        input_refs=(phase7_ref(31, "input"),),
        output_refs=(phase7_ref(32, "output"),),
        failure_refs=(phase7_ref(33, "failure"),),
        adapter_refs=(phase7_ref(25, "adapter"),),
        trace_refs=(phase7_ref(28, "execution_trace"),),
        permit_refs=(phase7_ref(11, "permit"),),
        replay_items=(("replay", "summary_only"),),
    )


def determinism_hint():
    return ExecutionDeterminismHint(
        determinism_hint_ref=phase7_ref(34, "determinism_hint"),
        action_ref=action_ref(),
        determinism_kind=DeterminismKind.MOSTLY_DETERMINISTIC,
        determinism_score_ref=phase7_ref(35, "determinism_score"),
    )


def idempotency_hint():
    return ExecutionIdempotencyHint(
        idempotency_hint_ref=phase7_ref(36, "idempotency_hint"),
        action_ref=action_ref(),
        idempotency_kind=IdempotencyKind.CONDITIONALLY_IDEMPOTENT,
        idempotency_score_ref=phase7_ref(37, "idempotency_score"),
    )


def side_effect_summary():
    return ExecutionSideEffectSummary(
        side_effect_summary_ref=phase7_ref(38, "side_effect_summary"),
        action_ref=action_ref(),
        side_effect_descriptor_refs=(phase7_ref(39, "side_effect_descriptor"),),
        summary_items=(("side_effect", "descriptor_ref_only"),),
    )


def reconciliation_advice():
    return ExecutionReconciliationAdvice(
        reconciliation_advice_ref=phase7_ref(40, "reconciliation_advice"),
        action_ref=action_ref(),
        result_ref=phase7_ref(41, "action_result"),
        failure_ref=phase7_ref(33, "failure"),
        recovery_requirement_ref=phase7_ref(9, "recovery_requirement"),
        advice_items=(("reconcile", "advice_only"),),
    )


def checkpoint_ref():
    return ExecutionCheckpointRef(
        checkpoint_ref=phase7_ref(42, "execution_checkpoint"),
        action_ref=action_ref(),
        trace_ref=phase7_ref(28, "execution_trace"),
    )


def snapshot_ref():
    checkpoint = checkpoint_ref()
    return ExecutionSnapshotRef(
        snapshot_ref=phase7_ref(43, "execution_snapshot"),
        action_ref=action_ref(),
        checkpoint_ref=checkpoint.checkpoint_ref,
    )


def operational_summary():
    return ExecutionOperationalSummary(
        operational_summary_ref=phase7_ref(44, "execution_operational_summary"),
        action_ref=action_ref(),
        transaction_ref=transaction_ref().transaction_ref,
        resource_budget_ref=resource_budget().resource_budget_ref,
        concurrency_scope_ref=concurrency_scope().concurrency_scope_ref,
        replay_summary_ref=replay_summary().replay_summary_ref,
        summary_items=(("operation", "summary_only"),),
    )


def l5_resource_feedback():
    return L4ToL5ResourceFeedback(
        feedback_ref=phase7_ref(45, "l4_to_l5_resource_feedback"),
        resource_budget_ref=resource_budget().resource_budget_ref,
        consumption_summary_ref=budget_summary().consumption_summary_ref,
        feedback_items=(("resource", "future_l5_recheck"),),
    )


def l6_recovery_replay_requirement():
    return L4ToL6RecoveryReplayRequirement(
        requirement_ref=phase7_ref(46, "l4_to_l6_recovery_replay_requirement"),
        recovery_requirement_ref=phase7_ref(9, "recovery_requirement"),
        replay_requirement_ref=replay_summary().replay_summary_ref,
        reconciliation_requirement_ref=reconciliation_advice().reconciliation_advice_ref,
        requirement_items=(("replay", "future_l6_requirement"),),
    )
