from l4_phase7_builders import (
    operational_summary,
    replay_summary,
    resource_budget,
    transaction_ref,
)
from tiangong_kernel.l4_action_grounding import (
    ExecutionReplaySummary,
    ExecutionTransactionRef,
    ResourceBudgetRef,
    action_grounding_stable_hash,
    action_grounding_to_primitive,
)


def test_l4_phase7_public_exports_and_stable_serialization():
    transaction = transaction_ref()
    budget = resource_budget()
    replay = replay_summary()
    operational = operational_summary()

    assert isinstance(transaction, ExecutionTransactionRef)
    assert isinstance(budget, ResourceBudgetRef)
    assert isinstance(replay, ExecutionReplaySummary)
    primitive = action_grounding_to_primitive(operational)
    digest = action_grounding_stable_hash(operational)

    assert primitive["summary_only"] is True
    assert primitive["commits_real_transaction"] is False
    assert len(digest) >= 32
