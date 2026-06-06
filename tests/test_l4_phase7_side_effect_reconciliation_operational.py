import pytest

from l4_phase7_builders import operational_summary, phase7_ref, reconciliation_advice, side_effect_summary
from tiangong_kernel.l4_action_grounding import (
    ExecutionOperationalSummary,
    ExecutionReconciliationAdvice,
    ExecutionSideEffectSummary,
)


def test_l4_phase7_summaries_do_not_operate_or_write_state():
    side_effect = side_effect_summary()
    reconciliation = reconciliation_advice()
    operational = operational_summary()

    assert side_effect.summary_only is True
    assert side_effect.makes_risk_decision is False
    assert side_effect.grants_permission is False
    assert side_effect.performs_side_effect is False
    assert side_effect.writes_audit_store is False
    assert reconciliation.advice_only is True
    assert reconciliation.executes_reconciliation is False
    assert reconciliation.verifies_state is False
    assert reconciliation.writes_l2_state is False
    assert reconciliation.writes_audit_store is False
    assert operational.summary_only is True
    assert operational.manages_real_resource is False
    assert operational.schedules_concurrency is False
    assert operational.commits_real_transaction is False
    assert operational.executes_replay is False
    assert operational.writes_l2_state is False


def test_l4_phase7_summaries_reject_operation_flags():
    with pytest.raises(ValueError):
        ExecutionSideEffectSummary(side_effect_summary_ref=phase7_ref(160, "side_effect_summary"), grants_permission=True)
    with pytest.raises(ValueError):
        ExecutionReconciliationAdvice(
            reconciliation_advice_ref=phase7_ref(161, "reconciliation_advice"),
            executes_reconciliation=True,
        )
    with pytest.raises(ValueError):
        ExecutionOperationalSummary(
            operational_summary_ref=phase7_ref(162, "execution_operational_summary"),
            schedules_concurrency=True,
        )
