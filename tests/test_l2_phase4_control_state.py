from tiangong_kernel.l2_state import (
    ControlConstraintState,
    ControlPlaneMode,
    ControlPlaneState,
    ControlPlaneStatus,
    ControlSignalState,
    ControlSignalStatus,
)
from tests.test_l2_phase4_serialization import build_phase4_objects, identity, status, typed


def test_l2_phase4_control_plane_expresses_statuses_and_mode_labels():
    for control_status in (
        ControlPlaneStatus.READY,
        ControlPlaneStatus.ACTIVE,
        ControlPlaneStatus.PAUSED,
        ControlPlaneStatus.BLOCKED,
        ControlPlaneStatus.DEGRADED,
        ControlPlaneStatus.LIMITED,
        ControlPlaneStatus.CLOSED,
    ):
        state = ControlPlaneState(
            identity=identity(500),
            status=status(),
            control_status=control_status,
            mode=ControlPlaneMode.READ_ONLY,
        )
        assert state.control_status is control_status
        assert state.mode is ControlPlaneMode.READ_ONLY


def test_l2_phase4_control_plane_links_run_task_tool_boundary_resource_and_security_refs():
    objects = build_phase4_objects()
    control = objects["control"]

    assert control.run_ref == objects["phase3"]["run"].identity.state_ref
    assert control.task_ref == objects["phase3"]["task"].identity.state_ref
    assert control.tool_intent_state_ref == objects["phase3"]["tool_intent"].identity.state_ref
    assert control.model_feedback_state_ref == objects["phase3"]["feedback"].identity.state_ref
    assert control.boundary_state_refs == (objects["boundary_check"].identity.state_ref,)
    assert control.resource_state_refs == (objects["budget"].identity.state_ref,)
    assert control.security_state_refs == (objects["security"].identity.state_ref,)


def test_l2_phase4_control_signal_and_constraint_are_reference_only():
    objects = build_phase4_objects()
    signal = objects["signal"]
    constraint = objects["constraint"]

    assert isinstance(signal, ControlSignalState)
    assert signal.signal_status is ControlSignalStatus.PENDING
    assert signal.target_refs == (objects["phase3"]["tool_intent"].identity.state_ref,)
    assert isinstance(constraint, ControlConstraintState)
    assert constraint.constraint_refs == (typed(185, "constraint"),)
    assert constraint.applies_to_refs[0] == objects["phase3"]["tool_intent"].identity.state_ref
