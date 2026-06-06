from tiangong_kernel.l2_state import (
    BoundaryBlockedState,
    BoundaryCheckState,
    BoundaryCheckStatus,
)
from tests.test_l2_phase4_serialization import build_phase4_objects, identity, status, typed


def test_l2_phase4_boundary_check_expresses_required_statuses():
    for check_status in (
        BoundaryCheckStatus.NOT_REQUIRED,
        BoundaryCheckStatus.PENDING,
        BoundaryCheckStatus.PASSED,
        BoundaryCheckStatus.BLOCKED,
        BoundaryCheckStatus.DEGRADED,
        BoundaryCheckStatus.ALTERNATIVE_AVAILABLE,
        BoundaryCheckStatus.CONFIRMATION_REQUIRED,
        BoundaryCheckStatus.EXPIRED,
    ):
        state = BoundaryCheckState(identity=identity(600), status=status(), check_status=check_status)
        assert state.check_status is check_status


def test_l2_phase4_boundary_check_records_external_refs_without_deciding():
    objects = build_phase4_objects()
    boundary = objects["boundary_check"]

    assert boundary.checked_subject_ref == objects["phase3"]["tool_intent"].identity.state_ref
    assert boundary.boundary_ref == typed(111, "boundary")
    assert boundary.risk_view_ref == typed(112, "risk_view")
    assert boundary.decision_ref == typed(113, "decision")
    assert boundary.policy_state_refs == (objects["policy"].identity.state_ref,)
    assert boundary.reason_code == "external_passed"


def test_l2_phase4_boundary_block_records_kind_and_recoverable_tags():
    blocked = build_phase4_objects()["blocked"]

    assert isinstance(blocked, BoundaryBlockedState)
    assert blocked.recoverable is True
    assert blocked.requires_upper_layer_action is True
    assert blocked.blocking_policy_refs
