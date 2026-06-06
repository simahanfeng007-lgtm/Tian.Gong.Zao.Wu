import pytest

from tiangong_kernel.l0_primitives.serialization import stable_json_dumps
from tiangong_kernel.l2_state import ObservationFrameKind, ObservationFrameState, ObservationFrameStatus
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status, typed


def test_l2_phase5_observation_frame_expresses_kinds_and_statuses():
    for frame_kind in (
        ObservationFrameKind.EVENT,
        ObservationFrameKind.METRIC,
        ObservationFrameKind.AUDIT,
        ObservationFrameKind.EFFECT,
        ObservationFrameKind.MODEL_FEEDBACK,
        ObservationFrameKind.BOUNDARY,
        ObservationFrameKind.SECURITY,
    ):
        state = ObservationFrameState(identity=identity(220), status=status(), frame_kind=frame_kind)
        assert state.frame_kind is frame_kind

    for frame_status in (
        ObservationFrameStatus.PARTIAL,
        ObservationFrameStatus.CONFLICTED,
        ObservationFrameStatus.REDACTED,
        ObservationFrameStatus.STALE,
    ):
        state = ObservationFrameState(identity=identity(221), status=status(), frame_status=frame_status)
        assert state.frame_status is frame_status


def test_l2_phase5_observation_frame_records_payload_ref_not_sensitive_payload():
    frame = build_phase5_chain()["frame"]
    payload = stable_json_dumps(frame)

    assert frame.observed_payload_ref == typed(32, "redacted_payload_ref")
    assert "sk-live-secret" not in payload
    assert "password" not in payload.lower()
    assert frame.observed_summary == "effect observation reference accepted"


def test_l2_phase5_observation_frame_rejects_long_raw_log_like_summary():
    with pytest.raises(ValueError):
        ObservationFrameState(identity=identity(222), status=status(), observed_summary="x" * 513)
