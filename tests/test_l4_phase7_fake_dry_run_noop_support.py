from l4_phase7_builders import action_ref, resource_budget
from tiangong_kernel.l4_action_grounding import (
    DryRunTransactionResourceSupport,
    FakeTransactionResourceSupport,
    NoOpTransactionResourceSupport,
)


def test_l4_phase7_fake_support_returns_refs_and_summaries_only():
    support = FakeTransactionResourceSupport()
    budget = resource_budget()
    transaction = support.transaction_ref(action_ref())
    commit = support.commit_intent(transaction.transaction_ref, action_ref())
    rollback = support.rollback_intent(transaction.transaction_ref, action_ref())
    usage = support.usage_report(action_ref(), budget)
    summary = support.budget_summary(budget, usage)
    replay = support.replay_summary(action_ref())

    assert support.test_only is True
    assert transaction.starts_real_transaction is False
    assert commit.executes_commit is False
    assert rollback.executes_rollback is False
    assert usage.reads_real_system_resource is False
    assert summary.deducts_real_quota is False
    assert replay.executes_replay is False


def test_l4_phase7_dry_run_and_noop_supports_do_not_manage_resources():
    dry_run = DryRunTransactionResourceSupport()
    no_op = NoOpTransactionResourceSupport()
    budget = resource_budget()

    preview = dry_run.resource_usage_preview(action_ref(), budget)
    advice = dry_run.reconciliation_advice(action_ref())
    usage = no_op.resource_usage_report(action_ref())
    replay = no_op.replay_summary(action_ref())

    assert dry_run.dry_run_only is True
    assert no_op.no_op_only is True
    assert preview.allocates_real_resource is False
    assert advice.executes_reconciliation is False
    assert usage.reads_real_system_resource is False
    assert replay.executes_replay is False
