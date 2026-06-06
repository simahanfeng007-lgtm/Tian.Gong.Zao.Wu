import pytest

from l4_phase8_builders import boundary_invariant_suite, phase8_ref
from tiangong_kernel.l4_execution import L4BoundaryInvariantSuite


def test_l4_phase8_boundary_invariant_suite_covers_key_boundaries():
    suite = boundary_invariant_suite()

    assert "NoLiveExecutionWithoutL5Invariant" in suite.invariant_names
    assert "NoL4PermissionDecisionInvariant" in suite.invariant_names
    assert "NoResourceBudgetAllocationInL4Invariant" in suite.invariant_names
    assert suite.suite_only is True
    assert suite.grants_permission is False
    assert suite.signs_permit is False
    assert suite.writes_l2_state is False
    assert suite.implements_l6_subsystem is False


def test_l4_phase8_boundary_invariant_suite_rejects_permission_flags():
    with pytest.raises(ValueError):
        L4BoundaryInvariantSuite(invariant_suite_ref=phase8_ref(130, "invariant_suite"), signs_permit=True)
