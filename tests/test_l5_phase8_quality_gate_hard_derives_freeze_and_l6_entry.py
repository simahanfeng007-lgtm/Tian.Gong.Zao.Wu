from tests.l5_phase8_factories import passing_quality_gate
import pytest


def test_l5_phase8_quality_gate_hard_derives_freeze_and_l6_entry():
    gate = passing_quality_gate(allow_freeze_l5=False, allow_enter_l6_general_plugins=False, allow_enter_l6_product_artifact_factory=False)
    assert gate.allow_freeze_l5 is True
    assert gate.allow_enter_l6_general_plugins is True
    assert gate.allow_enter_l6_product_artifact_factory is True
    blocked = passing_quality_gate(p1_count=1)
    assert blocked.allow_freeze_l5 is False
    assert blocked.allow_enter_l6_general_plugins is False


@pytest.mark.parametrize(
    "field_name",
    (
        "generic_plugin_host_precheck_passed",
        "capability_readiness_matrix_passed",
        "no_live_artifact_build_passed",
        "public_projection_second_leak_test_passed",
        "context_belief_world_boundary_passed",
        "context_safety_projection_passed",
        "l6_context_assembler_precondition_passed",
        "belief_event_precedence_passed",
        "world_state_evidence_staleness_passed",
        "tool_model_output_demotion_passed",
        "memory_injection_boundary_passed",
    ),
)
def test_l5_phase8_quality_gate_blocks_freeze_when_hard_input_fails(field_name):
    gate = passing_quality_gate(**{field_name: False})
    assert gate.allow_freeze_l5 is False
    assert gate.allow_enter_l6_general_plugins is False
    assert gate.allow_enter_l6_product_artifact_factory is False
    assert gate.allow_plan_l6_product_artifact_factory is False
    assert gate.allow_execute_product_artifact_factory is False
    assert f"quality_gate_failed:{field_name}" in gate.blocking_reasons


def test_l5_phase8_quality_gate_blocks_when_blocking_reasons_are_non_empty():
    gate = passing_quality_gate(blocking_reasons=("risk:manual_block",))
    assert gate.allow_freeze_l5 is False
    assert gate.allow_enter_l6_general_plugins is False
    assert gate.allow_enter_l6_product_artifact_factory is False
    assert "risk:manual_block" in gate.blocking_reasons
    assert "quality_gate_failed:blocking_reasons_empty" in gate.blocking_reasons


def test_l5_phase8_quality_gate_blocks_final_freeze_when_p2_or_p3_exist():
    assert passing_quality_gate(p2_count=1).allow_freeze_l5 is False
    assert passing_quality_gate(p3_count=1).allow_freeze_l5 is False
