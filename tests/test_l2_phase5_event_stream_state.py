import pytest

from tiangong_kernel.l2_state import EventStreamKind, EventStreamState, EventStreamStatus
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status


def test_l2_phase5_event_stream_expresses_statuses_and_counts():
    for stream_status in (
        EventStreamStatus.STREAMING,
        EventStreamStatus.INTERRUPTED,
        EventStreamStatus.TRUNCATED,
        EventStreamStatus.CLOSED,
    ):
        state = EventStreamState(identity=identity(230), status=status(), stream_status=stream_status)
        assert state.stream_status is stream_status

    stream = build_phase5_chain()["stream"]
    assert stream.stream_kind is EventStreamKind.RUN_EVENT_STREAM
    assert stream.frame_count == 3
    assert stream.dropped_frame_count == 1
    assert stream.redacted_frame_count == 1
    assert stream.latest_frame_ref == build_phase5_chain()["frame"].identity.state_ref


def test_l2_phase5_event_stream_rejects_negative_external_counts():
    with pytest.raises(ValueError):
        EventStreamState(identity=identity(231), status=status(), frame_count=-1)


def test_l2_phase5_event_stream_does_not_expose_stream_consumption_methods():
    stream = build_phase5_chain()["stream"]

    assert not hasattr(stream, "subscribe")
    assert not hasattr(stream, "consume")
    assert not hasattr(stream, "listen")
    assert not hasattr(stream, "poll")
