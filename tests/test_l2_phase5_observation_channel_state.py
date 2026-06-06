from tiangong_kernel.l2_state import ObservationChannelKind, ObservationChannelState, ObservationChannelStatus
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status


def test_l2_phase5_observation_channel_expresses_kinds_and_statuses():
    for channel_kind in (
        ObservationChannelKind.DIRECT_STATE_INPUT,
        ObservationChannelKind.EVENT_PROJECTION,
        ObservationChannelKind.AUDIT_PROJECTION,
        ObservationChannelKind.METRIC_PROJECTION,
    ):
        state = ObservationChannelState(identity=identity(210), status=status(), channel_kind=channel_kind)
        assert state.channel_kind is channel_kind

    for channel_status in (
        ObservationChannelStatus.OPEN,
        ObservationChannelStatus.INTERRUPTED,
        ObservationChannelStatus.CLOSED,
        ObservationChannelStatus.EXPIRED,
    ):
        state = ObservationChannelState(identity=identity(211), status=status(), channel_status=channel_status)
        assert state.channel_status is channel_status


def test_l2_phase5_observation_channel_records_inputs_without_transport_methods():
    objects = build_phase5_chain()
    channel = objects["channel"]

    assert channel.source_state_refs == (objects["source"].identity.state_ref,)
    assert channel.boundary_state_refs == (objects["phase4"]["boundary_check"].identity.state_ref,)
    assert channel.resource_state_refs == (objects["phase4"]["budget"].identity.state_ref,)
    assert channel.security_state_refs == (objects["phase4"]["security"].identity.state_ref,)
    assert channel.expected_observation_kinds == ("effect", "boundary")
    assert not hasattr(channel, "subscribe")
    assert not hasattr(channel, "publish")
    assert not hasattr(channel, "consume")
    assert not hasattr(channel, "listen")
    assert not hasattr(channel, "poll")
