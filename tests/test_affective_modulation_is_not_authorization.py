from tests.l5_phase8_factories import passing_quality_gate
from tiangong_kernel.l5_plugin_host import AffectiveModulationContractBinding, L5FinalQualityGateDecision


def test_affective_modulation_is_not_authorization():
    binding = AffectiveModulationContractBinding()
    assert binding.advisory_only_ref
    assert binding.no_execution_order_ref
    assert "forbid:affective_state_as_authorization" in binding.forbidden_misuse_refs


def test_final_quality_gate_hard_derives_affective_planning_only():
    gate = passing_quality_gate()
    assert gate.allow_enter_l6_affective_plugin is True
    assert gate.allow_plan_l6_affective_plugin is True
    assert gate.allow_execute_l6_affective_plugin is False
    assert gate.affective_plugin_scope == "l6_planning_only"


def test_final_quality_gate_blocks_affective_when_special_gate_fails():
    gate = passing_quality_gate(affective_public_projection_passed=False)
    assert gate.allow_freeze_l5 is False
    assert gate.allow_enter_l6_affective_plugin is False
    assert "quality_gate_failed:affective_public_projection_passed" in gate.blocking_reasons


def test_final_quality_gate_cannot_be_manually_forced_for_affective_execution():
    gate = L5FinalQualityGateDecision(
        allow_enter_l6_affective_plugin=True,
        allow_plan_l6_affective_plugin=True,
        allow_execute_l6_affective_plugin=True,
    )
    assert gate.allow_enter_l6_affective_plugin is False
    assert gate.allow_plan_l6_affective_plugin is False
    assert gate.allow_execute_l6_affective_plugin is False
