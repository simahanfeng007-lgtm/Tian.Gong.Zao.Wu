import pytest

from tiangong_kernel.l2_state import (
    ObservationProjectionKind,
    ObservationProjectionState,
    ObservationProjectionStatus,
)
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status


def test_l2_phase5_observation_projection_expresses_kinds_and_statuses():
    for projection_kind in (
        ObservationProjectionKind.RUN_OBSERVATION_PROJECTION,
        ObservationProjectionKind.TASK_OBSERVATION_PROJECTION,
        ObservationProjectionKind.SKILL_OBSERVATION_PROJECTION,
        ObservationProjectionKind.TOOL_OBSERVATION_PROJECTION,
        ObservationProjectionKind.BOUNDARY_OBSERVATION_PROJECTION,
        ObservationProjectionKind.SECURITY_OBSERVATION_PROJECTION,
        ObservationProjectionKind.QUALITY_OBSERVATION_PROJECTION,
        ObservationProjectionKind.AUDIT_OBSERVATION_PROJECTION,
    ):
        state = ObservationProjectionState(identity=identity(270), status=status(), projection_kind=projection_kind)
        assert state.projection_kind is projection_kind

    for projection_status in (
        ObservationProjectionStatus.BUILT,
        ObservationProjectionStatus.PARTIAL,
        ObservationProjectionStatus.STALE,
        ObservationProjectionStatus.REDACTED,
        ObservationProjectionStatus.CONFLICTED,
    ):
        state = ObservationProjectionState(identity=identity(271), status=status(), projection_status=projection_status)
        assert state.projection_status is projection_status


def test_l2_phase5_observation_projection_records_structured_short_refs_only():
    objects = build_phase5_chain()
    projection = objects["projection"]

    assert projection.source_frame_refs == (objects["frame"].identity.state_ref,)
    assert projection.source_stream_refs == (objects["stream"].identity.state_ref,)
    assert projection.source_metric_refs == (objects["metric"].identity.state_ref,)
    assert projection.source_audit_refs == (objects["audit"].identity.state_ref,)
    assert projection.quality_state_refs == (objects["quality"].identity.state_ref,)
    assert projection.projected_status_summary == "partial observation"
    assert not hasattr(projection, "generate_prompt")
    assert not hasattr(projection, "choose_next_action")


def test_l2_phase5_observation_projection_rejects_long_chat_like_summary():
    with pytest.raises(ValueError):
        ObservationProjectionState(
            identity=identity(272),
            status=status(),
            projected_observation_summary="x" * 513,
        )
