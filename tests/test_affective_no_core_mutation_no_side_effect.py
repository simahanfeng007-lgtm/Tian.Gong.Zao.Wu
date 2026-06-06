import pytest

from tiangong_kernel.l5_plugin_host import AffectivePluginMountDeclaration, AffectiveSafetyBoundaryRef, L5FinalInvariantSuite


def test_affective_no_core_mutation_no_side_effect():
    mount = AffectivePluginMountDeclaration()
    safety = AffectiveSafetyBoundaryRef()
    assert mount.no_core_mutation_ref
    assert mount.no_side_effect_ref
    assert "forbid:affective_core_mutation" in safety.forbidden_misuse_refs
    assert "forbid:affective_side_effect" in safety.forbidden_misuse_refs


def test_affective_mount_rejects_core_mutation_or_live_locator_values():
    with pytest.raises(ValueError):
        AffectivePluginMountDeclaration(safety_boundary_ref="https://example.invalid/live")


def test_l5_final_invariants_include_affective_boundaries():
    suite = L5FinalInvariantSuite()
    assert suite.affective_plugin_l6_planning_only is True
    assert suite.affective_state_not_authorization is True
    assert suite.affective_no_policy_bypass is True
    assert suite.affective_no_core_mutation is True
    assert suite.affective_no_side_effect is True
