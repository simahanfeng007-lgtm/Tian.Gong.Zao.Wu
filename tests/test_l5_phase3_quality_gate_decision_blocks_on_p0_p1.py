import pytest

from tiangong_kernel.l5_plugin_host import L5Phase3QualityGateDecision


def test_phase3_quality_gate_decision_blocks_when_p1_exists():
    with pytest.raises(ValueError):
        L5Phase3QualityGateDecision(
            p1_count=1,
            compileall_passed=True,
            collect_only_passed=True,
            targeted_pytest_passed=True,
            plugin_host_subset_passed=True,
            full_pytest_passed=True,
            forbidden_scan_passed=True,
            l0_l4_hash_clean=True,
            l5_phase1_phase2_hash_clean=True,
            zip_integrity_passed=True,
            registry_quality_gate_passed=True,
            snapshot_delta_determinism_passed=True,
            public_projection_safety_passed=True,
            allow_enter_l5_phase4=True,
        )
