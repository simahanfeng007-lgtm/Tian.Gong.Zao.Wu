from __future__ import annotations

from pathlib import Path

from tiangong_kernel.l1_ports.math_engine_contract_ports import ScoreResult
from tiangong_kernel.l4_action_grounding.math_model_adapter import BaseMathModelAdapter


def test_math_model_score_result_cannot_execute_or_grant_permission() -> None:
    result = ScoreResult()

    assert result.advisory_only is True
    assert result.authority_result is False
    for forbidden_attribute in ("action_enabled", "grants_permission", "writes_l2_state", "executes_tool"):
        assert not hasattr(result, forbidden_attribute)


def test_l4_math_adapter_invocation_cannot_turn_model_output_into_action() -> None:
    invocation = BaseMathModelAdapter().run_disabled()

    assert invocation.action_enabled is False
    assert invocation.real_calculation_performed is False
    assert invocation.external_call_performed is False
    assert invocation.adapter_descriptor.turns_score_into_action is False
    assert invocation.adapter_descriptor.grants_permission is False


def test_l1_math_engine_contract_does_not_use_final_decision_field() -> None:
    source = Path("tiangong_kernel/l1_ports/math_engine_contract_ports.py").read_text(encoding="utf-8")

    assert "final_decision" not in source
