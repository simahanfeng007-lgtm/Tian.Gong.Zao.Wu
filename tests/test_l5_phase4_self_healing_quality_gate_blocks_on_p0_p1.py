import pytest
from tiangong_kernel.l5_plugin_host import PluginSelfHealingQualityGateDecision


def test_self_healing_quality_gate_blocks_on_p0():
    with pytest.raises(ValueError):
        PluginSelfHealingQualityGateDecision(
            p0_count=1,
            failure_fault_link_passed=True,
            diagnosis_chain_passed=True,
            recovery_plan_declaration_passed=True,
            checkpoint_recovery_point_passed=True,
            transaction_compensation_passed=True,
            audit_evidence_passed=True,
            validation_regression_required_passed=True,
            no_live_recovery_execution_passed=True,
            public_projection_safety_passed=True,
            allow_enter_l5_phase5=True,
        )
