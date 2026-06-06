from __future__ import annotations

import pytest

from tiangong_agent_runtime.budget_low_friction_governance import (
    BudgetLowFrictionDecision,
    BudgetLowFrictionGovernanceBridge,
    BudgetPressureSignal,
)
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _budget_snapshot(exhausted: bool = False):
    return {
        "snapshot_id": "budget:test:l6_44",
        "step_ledger": {
            "max_steps": 10,
            "planned_steps": 4,
            "executed_steps_seen": 5,
            "remaining_steps": 5,
            "exhausted": exhausted,
        },
        "chain_lease": {"requested_extension": 0, "renewal_recommended": False},
        "timeout_budget": {"default_timeout_seconds": 100.0, "remaining_timeout_seconds": 25.0, "blocks_execution": False},
        "failure_budget": {"max_failures": 3, "observed_failures": 1, "exhausted": False},
        "planner_budget_hint": "A0-A4 low friction",
        "resource_exhausted": exhausted,
        "downgrade_required": False,
    }


def test_a0_a4_low_friction_budget_pressure_does_not_default_block() -> None:
    bridge = BudgetLowFrictionGovernanceBridge()
    report = bridge.evaluate(
        [
            ToolInvocation("return_analysis", {"content": "safe"}),
            ToolInvocation("write_workspace_file", {"path": "draft.txt", "content": "ok"}),
            ToolInvocation("write_workspace_file", {"path": "/needs-confirm.txt", "content": "ok"}),
        ],
        budget_snapshot=_budget_snapshot(exhausted=True),
    )
    decision = report.decision
    assert decision.passed is True
    assert len(decision.low_friction_steps) == 2
    assert len(decision.confirmation_steps) == 1
    assert len(decision.hard_blocked_steps) == 0
    assert decision.pressure_signal.resource_exhausted is True
    assert decision.pressure_signal.lease_renewal_recommended is True
    assert decision.a0_a4_low_friction_preserved is True
    assert report.no_budget_mutation is True


def test_a5_and_sensitive_credentials_remain_hard_blocked() -> None:
    bridge = BudgetLowFrictionGovernanceBridge()
    report = bridge.evaluate(
        [
            ToolInvocation("unknown_tool", {"content": "x"}),
            ToolInvocation("return_analysis", {"api_key": "sk-test"}),
            ToolInvocation("return_analysis", {"content": "authorization: bearer abc"}),
        ],
        budget_snapshot=_budget_snapshot(),
    )
    assert report.decision.passed is False
    assert len(report.decision.hard_blocked_steps) == 3
    rendered = str(report.public_dict()).lower()
    assert "a5" in rendered
    assert "sensitive" in rendered
    assert report.decision.a5_hard_boundary_preserved is True
    assert report.decision.credential_privacy_hard_gate_preserved is True


def test_release_activation_merge_or_irreversible_steps_are_strong_gated_not_auto_allowed() -> None:
    bridge = BudgetLowFrictionGovernanceBridge()
    report = bridge.evaluate(
        [
            ToolInvocation("create_release_bundle", {"name": "candidate"}),
            ToolInvocation("write_workspace_file", {"path": "patch.txt", "content": "merge to stable after approval"}),
        ],
        budget_snapshot=_budget_snapshot(),
    )
    assert report.decision.passed is True
    assert len(report.decision.strong_gate_steps) == 2
    assert len(report.decision.low_friction_steps) == 0
    assert report.decision.irreversible_release_activation_merge_gate_preserved is True
    assert all(item["requires_quality_gate"] is True for item in report.decision.strong_gate_steps)


def test_pressure_signal_rejects_bool_scores_and_decision_rejects_boundary_false() -> None:
    with pytest.raises(ValueError):
        BudgetPressureSignal(signal_id="bad", step_pressure_score=True)  # type: ignore[arg-type]
    signal = BudgetPressureSignal(signal_id="ok")
    with pytest.raises(ValueError):
        BudgetLowFrictionDecision(
            decision_id="bad",
            pressure_signal=signal,
            no_budget_mutation=False,
        )


def test_public_report_is_planner_consumable_and_non_executing() -> None:
    bridge = BudgetLowFrictionGovernanceBridge()
    report = bridge.evaluate([ToolInvocation("return_analysis", {"content": "ok"})], budget_snapshot=_budget_snapshot())
    payload = report.public_dict()
    assert payload["planner_consumable"] is True
    assert payload["no_second_runtime"] is True
    assert payload["no_permit_override"] is True
    assert payload["no_direct_execution"] is True
    assert payload["no_tool_dispatch"] is True
    assert "A0-A4" in payload["planner_hint"]
