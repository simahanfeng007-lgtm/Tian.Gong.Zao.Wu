import pytest
from tiangong_kernel.l5_plugin_host import PluginLifecycleQualityGateDecision


def test_quality_gate_decision_blocks_on_p0_or_p1():
    with pytest.raises(ValueError):
        PluginLifecycleQualityGateDecision(
            p0_count=1,
            p1_count=0,
            lifecycle_validation_passed=True,
            mount_declaration_validation_passed=True,
            no_live_execution_passed=True,
            public_projection_safety_passed=True,
            registry_phase3_compatibility_passed=True,
            l0_l4_hash_clean=True,
            l5_phase1_phase3_hash_clean=True,
            full_pytest_passed=True,
            forbidden_scan_passed=True,
            allow_enter_l5_phase5=True,
            decision_ref="decision:l5_phase4",
            actor_ref="actor:l5",
            scope_ref="scope:l5",
            trace_ref="trace:l5",
            policy_ref="policy:l5",
            approval_ref="approval:l5",
            evidence_refs=("evidence:l5",),
            provenance_refs=("provenance:l5",),
            accountability_ref="accountability:l5",
            tamper_evidence_ref="tamper:l5",
            quality_gate_event_ref="event:l5",
        )
